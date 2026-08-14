#!/usr/bin/env python3
"""
PNG to JPEG Compression Tuning Server
A FastAPI web application to tune and batch-process PNG-to-JPEG compression
using ImageMagick (`magick`).

The UI is server-side rendered (SSR) with minimal JavaScript and CSS.
Images shown/processed are filtered to those referenced in the annales TSV.
"""

import os
import sys
import csv
import html
import time
import queue
import shutil
import pathlib
import tempfile
import threading
import subprocess
import webbrowser

from urllib.parse import urlencode
from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from PIL import Image

DEFAULT_PORT = 8000

ANNALES_TSV = (
    pathlib.Path(__file__).resolve().parent.parent
    / "site"
    / "static"
    / "annales-bia.tsv"
)

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif")


def tsv_attachment_links() -> set[str] | None:
    """Return the attachment_link stems referenced in the annales TSV.

    Returns None (filter disabled) if the TSV cannot be read.
    """
    try:
        with open(ANNALES_TSV, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            return {
                row["attachment_link"].strip()
                for row in reader
                if row.get("attachment_link")
            }
    except Exception as e:
        print(f"Warning: could not read {ANNALES_TSV}: {e}")
    return None


def is_referenced_in_tsv(item: pathlib.Path, links: set[str] | None) -> bool:
    return links is None or item.stem in links


def select_directory(title="Select Directory"):
    """
    Opens system native Finder / File Explorer folder chooser dialog.
    Supports Tkinter, macOS osascript, Linux zenity/kdialog, Windows PowerShell dialogs.
    """
    # 1. Try tkinter (standard Python GUI)
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        if folder:
            return folder
    except Exception:
        pass

    # 2. Try macOS osascript (AppleScript Finder folder picker)
    if sys.platform == "darwin":
        try:
            cmd = [
                "osascript",
                "-e",
                f'POSIX path of (choose folder with prompt "{title}")',
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    # 3. Try Linux zenity / kdialog
    if sys.platform.startswith("linux"):
        if shutil.which("zenity"):
            try:
                cmd = ["zenity", "--file-selection", "--directory", f"--title={title}"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass
        if shutil.which("kdialog"):
            try:
                cmd = ["kdialog", "--getexistingdirectory", ".", f"--title={title}"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass

    # 4. Try Windows PowerShell folder picker dialog
    if sys.platform == "win32":
        try:
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f'$dialog.Description = "{title}"; '
                "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $dialog.SelectedPath }"
            )
            res = subprocess.run(
                ["powershell", "-Command", ps_script], capture_output=True, text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    return None


# Tkinter (and other GUI) dialogs must run on the main thread on macOS/Linux.
# FastAPI sync endpoints run on a threadpool, so directory selection is
# dispatched to the main thread through a queue (serviced in run_server).
_dialog_queue: queue.Queue = queue.Queue()
_dialog_results: queue.Queue = queue.Queue()


def request_directory_selection(title: str):
    _dialog_queue.put(title)
    return _dialog_results.get()


def service_dialog_queue() -> None:
    try:
        title = _dialog_queue.get_nowait()
    except queue.Empty:
        return
    folder = select_directory(title=title)
    _dialog_results.put(folder)


app = FastAPI(title="PNG to JPEG Magick Tuner")


def json_error(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def list_images(directory: pathlib.Path) -> tuple[list[dict], bool]:
    links = tsv_attachment_links()
    images = []
    for item in sorted(directory.iterdir()):
        if item.is_file() and item.suffix.lower() == ".png":
            if not is_referenced_in_tsv(item, links):
                continue
            images.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                }
            )
    return images, links is not None


def compress_image(
    path: str, quality: str, sampling_factor: str
) -> tuple[bytes, int] | None:
    tmp_output = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as tmp_file:
            tmp_output = tmp_file.name
        cmd = [
            "magick",
            path,
            "-sampling-factor",
            sampling_factor,
            "-quality",
            quality,
            tmp_output,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return None
        size = os.path.getsize(tmp_output)
        with open(tmp_output, "rb") as f:
            data = f.read()
        return data, size
    except (FileNotFoundError, OSError):
        return None
    finally:
        if tmp_output and os.path.exists(tmp_output):
            try:
                os.remove(tmp_output)
            except OSError:
                pass


def process_batch(
    input_dir_str: str,
    output_dir_str: str,
    suffix: str,
    quality: str,
    sampling_factor: str,
) -> tuple[int, dict]:
    if not output_dir_str:
        return 400, {"error": "Output directory is mandatory."}
    if not input_dir_str:
        return 400, {"error": "Input directory is required."}

    input_dir = pathlib.Path(input_dir_str).expanduser().resolve()
    output_dir = pathlib.Path(output_dir_str).expanduser().resolve()

    if not input_dir.is_dir():
        return 400, {"error": f"Input directory does not exist: {input_dir_str}"}

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return 400, {"error": f"Failed to create output directory: {e}"}

    links = tsv_attachment_links()
    img_files = [
        f
        for f in sorted(input_dir.iterdir())
        if f.is_file()
        and f.suffix.lower().endswith(IMAGE_SUFFIXES)
        and is_referenced_in_tsv(f, links)
    ]
    if not img_files:
        if links is None:
            return 400, {"error": "No PNG images found in input directory."}
        return 400, {
            "error": "No images referenced in annales-bia.tsv found in input directory."
        }

    processed_count = 0
    total_orig_bytes = 0
    total_comp_bytes = 0

    for img_file in img_files:
        result = compress_image(str(img_file), quality, sampling_factor)
        if result is None:
            return 400, {"error": f"Magick error on {img_file.name}"}
        data, comp_size = result
        (output_dir / (img_file.stem + suffix)).write_bytes(data)
        total_orig_bytes += img_file.stat().st_size
        total_comp_bytes += comp_size
        processed_count += 1

    savings_pct = 0.0
    if total_orig_bytes > 0:
        savings_pct = round(
            ((total_orig_bytes - total_comp_bytes) / total_orig_bytes) * 100, 1
        )

    return 200, {
        "processed": processed_count,
        "total_orig_bytes": total_orig_bytes,
        "total_comp_bytes": total_comp_bytes,
        "savings_percent": savings_pct,
    }


def image_size(path: str) -> tuple[int, int] | None:
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def fmt_bytes(n: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024 or unit == "GB":
            return f"{n:.0f} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


#############
# API routes #
#############


@app.get("/api/images")
def api_images(dir: str = Query(default="")) -> JSONResponse:
    if not dir:
        return json_error(400, "Directory path is required.")
    dir_path = pathlib.Path(dir).expanduser().resolve()
    if not dir_path.is_dir():
        return json_error(400, f"Directory non-existent or invalid: {dir}")
    images, filtered = list_images(dir_path)
    return JSONResponse({"images": images, "filtered": filtered})


@app.get("/api/original")
def api_original(path: str = Query(default="")) -> Response:
    if not path:
        return json_error(400, "Path is required.")
    img_path = pathlib.Path(path)
    if not img_path.is_file():
        return json_error(404, f"File not found: {path}")
    try:
        return Response(content=img_path.read_bytes(), media_type="image/png")
    except Exception as e:
        return json_error(500, f"Error reading file: {e}")


@app.get("/api/preview")
def api_preview(
    path: str = Query(default=""),
    quality: str = Query(default="10"),
    sampling_factor: str = Query(default="4:4:4"),
) -> Response:
    if not path:
        return json_error(400, "Image path is required.")
    img_path = pathlib.Path(path)
    if not img_path.is_file():
        return json_error(404, f"Image file not found: {path}")
    if shutil.which("magick") is None:
        return json_error(
            500,
            "Command 'magick' not found. Please ensure ImageMagick is installed and in your PATH.",
        )
    result = compress_image(str(img_path), quality, sampling_factor)
    if result is None:
        return json_error(500, f"Magick error on {path}")
    data, comp_size = result
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={
            "X-Original-Size": str(img_path.stat().st_size),
            "X-Compressed-Size": str(comp_size),
            "Access-Control-Expose-Headers": "X-Original-Size, X-Compressed-Size",
            "Cache-Control": "no-cache",
        },
    )


@app.post("/api/select-dir")
def api_select_dir(payload: dict | None = None) -> JSONResponse:
    title = (payload or {}).get("title", "Select Directory")
    folder = request_directory_selection(title=title)
    if folder:
        return JSONResponse({"path": folder})
    return JSONResponse({"path": None, "cancelled": True})


@app.post("/api/batch")
def api_batch(payload: dict) -> JSONResponse:
    status, result = process_batch(
        str(payload.get("input_dir", "")).strip(),
        str(payload.get("output_dir", "")).strip(),
        str(payload.get("suffix", "_minified.jpeg")),
        str(payload.get("quality", 10)),
        str(payload.get("sampling_factor", "4:4:4")),
    )
    return JSONResponse(result, status_code=status)


#############
# SSR page  #
#############

PAGE_CSS = """\
*{box-sizing:border-box}
body{font-family:system-ui,sans-serif;margin:1.2rem;color:#111;max-width:1500px}
h1{font-size:1.3rem}
.toolbar{display:flex;flex-wrap:wrap;gap:.5rem;align-items:flex-end;margin:1rem 0;padding:.75rem;border:1px solid #ddd;border-radius:8px}
.field{display:flex;flex-direction:column;gap:.15rem}
label{font-size:.75rem;color:#555}
input,select,button{padding:.35rem .5rem;border:1px solid #bbb;border-radius:4px;font-size:.85rem}
.actions{display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0}
.grid{display:flex;flex-wrap:wrap;gap:.2rem;margin:.5rem 0}
.grid a{padding:.1rem .35rem;border:1px solid #ccc;border-radius:3px;text-decoration:none;color:#111;font-size:.75rem}
.grid a.active{background:#dbeafe;border-color:#3b82f6}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.pair figure{margin:0}
.pair figcaption{font-size:.8rem;color:#555;margin-bottom:.25rem}
.pair img{max-width:100%;height:auto;border:1px solid #ccc}
.stats{color:#555;font-size:.85rem}
.err{color:#b91c1c}
"""

PAGE_JS = """\
const QUALITY_STEP = 5;

function shortcutsEnabled() {
  const tag = document.activeElement ? document.activeElement.tagName : '';
  return !['INPUT', 'SELECT', 'TEXTAREA'].includes(tag);
}

function form() {
  return document.getElementById('main-form');
}

function qualityField() {
  return document.getElementById('quality');
}

function gotoQuality(delta) {
  const q = parseInt(qualityField().value, 10) || 10;
  qualityField().value = Math.max(1, Math.min(100, q + delta));
  form().submit();
}

function gotoImage(offset) {
  const link = offset < 0
    ? document.getElementById('nav-prev')
    : document.getElementById('nav-next');
  if (link) location.href = link.getAttribute('href');
}

function showOriginal(show) {
  const fig = document.getElementById('figure-comp');
  if (fig) fig.style.display = show ? 'none' : '';
}

async function browse(id, title) {
  try {
    const res = await fetch('/api/select-dir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title })
    });
    const data = await res.json();
    if (data.path) {
      document.getElementById(id).value = data.path;
      form().submit();
    }
  } catch (err) {
    alert('Directory picker failed: ' + err.message);
  }
}

document.addEventListener('keydown', (e) => {
  if (!shortcutsEnabled()) return;
  if (e.code === 'Space') {
    e.preventDefault();
    showOriginal(true);
  } else if (e.code === 'ArrowUp') {
    e.preventDefault();
    gotoQuality(QUALITY_STEP);
  } else if (e.code === 'ArrowDown') {
    e.preventDefault();
    gotoQuality(-QUALITY_STEP);
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault();
    gotoImage(-1);
  } else if (e.code === 'ArrowRight') {
    e.preventDefault();
    gotoImage(1);
  }
});

document.addEventListener('keyup', (e) => {
  if (e.code === 'Space') showOriginal(false);
});

window.addEventListener('blur', () => showOriginal(false));
"""


def page_url(dir: str, out: str, suffix: str, sf: str, quality: str, index: int) -> str:
    return "/?" + urlencode(
        {
            "dir": dir,
            "out": out,
            "suffix": suffix,
            "sf": sf,
            "quality": quality,
            "index": index,
        }
    )


def render_toolbar(
    dir: str, out: str, suffix: str, sf: str, quality: str, index: int
) -> str:
    sf_options = ""
    for opt in ["4:4:4", "4:2:2", "4:2:0", "4:0:0"]:
        selected = " selected" if opt == sf else ""
        sf_options += f"<option value='{opt}'{selected}>{opt}</option>"
    return f"""
<form id='main-form' method='get' action='/'>
  <div class='toolbar'>
    <input type='hidden' name='index' value='{index}'>
    <div class='field'><label>Input directory</label><div><input name='dir' id='input-dir' value='{html.escape(dir)}'><button type='button' onclick="browse('input-dir','Select Input Directory containing PNGs')">Browse&hellip;</button></div></div>
    <div class='field'><label>Output directory</label><div><input name='out' id='output-dir' value='{html.escape(out)}'><button type='button' onclick="browse('output-dir','Select Mandatory Output Directory')">Browse&hellip;</button></div></div>
    <div class='field'><label>Suffix</label><input name='suffix' value='{html.escape(suffix)}'></div>
    <div class='field'><label>Sampling factor</label><select name='sf'>{sf_options}</select></div>
    <div class='field'><label>Quality</label><input name='quality' id='quality' type='number' min='1' max='100' value='{html.escape(quality)}'></div>
    <div class='field'><label>&nbsp;</label><button type='submit'>Apply</button></div>
  </div>
</form>"""


def render_content(
    dir: str, out: str, suffix: str, sf: str, quality: str, index: int
) -> str:
    if not dir:
        return "<p>Enter an input directory to list the PNG images referenced in annales-bia.tsv.</p>"
    dir_path = pathlib.Path(dir).expanduser().resolve()
    if not dir_path.is_dir():
        return (
            f"<p class='err'>Directory non-existent or invalid: {html.escape(dir)}</p>"
        )
    images, filtered = list_images(dir_path)
    if not images:
        msg = (
            "No PNG images referenced in annales-bia.tsv found in the specified directory."
            if filtered
            else "No PNG images found in the specified directory."
        )
        return f"<p class='err'>{msg}</p>"

    index = max(0, min(index, len(images) - 1))
    current = images[index]
    prev_index = (index - 1) % len(images)
    next_index = (index + 1) % len(images)

    links = []
    for i, img in enumerate(images):
        active = " active" if i == index else ""
        links.append(
            f"<a class='thumb{active}' href='{page_url(dir, out, suffix, sf, quality, i)}'>{i}</a>"
        )
    grid = f"<div class='grid'>{''.join(links)}</div>"

    dim = image_size(current["path"])
    dim_html = f" ({dim[0]} &times; {dim[1]} px)" if dim else ""
    count = (
        f"<p>Image {index + 1} of {len(images)} &mdash; "
        f"<strong>{html.escape(current['name'])}</strong>{dim_html}</p>"
    )

    nav = (
        f"<div class='actions'>"
        f"<a id='nav-prev' href='{page_url(dir, out, suffix, sf, quality, prev_index)}'>&larr; Prev</a>"
        f"<a id='nav-next' href='{page_url(dir, out, suffix, sf, quality, next_index)}'>Next &rarr;</a>"
        f"</div>"
    )

    orig_url = "/api/original?" + urlencode({"path": current["path"]})
    figure_orig = (
        f"<figure><figcaption>Original</figcaption>"
        f"<img src='{orig_url}' alt='{html.escape(current['name'])}'></figure>"
    )

    stats_html = ""
    figure_comp = ""
    if shutil.which("magick") is None:
        stats_html = "<p class='err'>magick not found in PATH.</p>"
    else:
        result = compress_image(current["path"], quality, sf)
        if result is None:
            stats_html = "<p class='err'>Magick could not compress this image.</p>"
        else:
            _, comp_size = result
            preview_url = "/api/preview?" + urlencode(
                {"path": current["path"], "quality": quality, "sampling_factor": sf}
            )
            figure_comp = (
                f"<figure id='figure-comp'><figcaption>Compressed (Q{html.escape(quality)}, "
                f"{html.escape(sf)})</figcaption><img src='{preview_url}'></figure>"
            )
            savings = (1 - comp_size / current["size"]) * 100 if current["size"] else 0
            stats_html = (
                f"<p class='stats'>Original {fmt_bytes(current['size'])} &rarr; "
                f"Compressed {fmt_bytes(comp_size)} ({savings:.1f}% smaller)</p>"
            )
    pair = f"<div class='pair'>{figure_orig}{figure_comp}</div>"

    batch_form = f"""
    <form method='post' action='/batch'>
      <input type='hidden' name='input_dir' value='{html.escape(dir)}'>
      <input type='hidden' name='output_dir' value='{html.escape(out)}'>
      <input type='hidden' name='suffix' value='{html.escape(suffix)}'>
      <input type='hidden' name='quality' value='{html.escape(quality)}'>
      <input type='hidden' name='sampling_factor' value='{html.escape(sf)}'>
      <button type='submit'>Batch compress all</button>
    </form>"""

    return f"{count}{nav}{grid}{pair}{stats_html}{batch_form}"


def render_page(
    dir: str, out: str, suffix: str, sf: str, quality: str, index: int
) -> str:
    toolbar = render_toolbar(dir, out, suffix, sf, quality, index)
    content = render_content(dir, out, suffix, sf, quality, index)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PNG to JPEG Magick Tuner</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<h1>&#128444; PNG to JPEG Magick Tuner</h1>
<p class='stats'>Keyboard: Space = view original &middot; &uarr;/&darr; = quality &plusmn;5 &middot; &larr;/&rarr; = prev/next</p>
{toolbar}
{content}
<script>{PAGE_JS}</script>
</body>
</html>"""


def render_batch_result(result: dict) -> str:
    if "error" in result:
        body = (
            f"<p class='err'>{html.escape(result['error'])}</p>"
            "<p><a href='/'>Back</a></p>"
        )
    else:
        body = (
            f"<p>Compressed {result['processed']} images, "
            f"saved {result['savings_percent']}% space overall.</p>"
            "<p><a href='/'>Back to tuner</a></p>"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Batch compress</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<h1>Batch compress</h1>
{body}
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def index(
    dir: str = Query(default=""),
    out: str = Query(default=""),
    suffix: str = Query(default="_minified.jpeg"),
    sf: str = Query(default="4:4:4"),
    quality: str = Query(default="10"),
    index: int = Query(default=0),
) -> str:
    return render_page(dir, out, suffix, sf, quality, index)


@app.post("/batch", response_class=HTMLResponse)
def batch(
    input_dir: str = Form(""),
    output_dir: str = Form(""),
    suffix: str = Form("_minified.jpeg"),
    quality: str = Form("10"),
    sampling_factor: str = Form("4:4:4"),
) -> str:
    status, result = process_batch(
        input_dir, output_dir, suffix, quality, sampling_factor
    )
    return render_batch_result(result)


def open_browser(port):
    """Opens the web browser pointing to localhost."""
    webbrowser.open(f"http://localhost:{port}")


def run_server(port=DEFAULT_PORT):
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    httpd_thread = threading.Thread(target=server.run, daemon=True)
    httpd_thread.start()

    # Automatically open in browser upon launch
    threading.Timer(0.5, open_browser, args=(port,)).start()

    print(f"🚀 PNG to JPEG Magick Tuner running on http://localhost:{port}")
    try:
        while True:
            service_dialog_queue()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.should_exit = True
        httpd_thread.join(timeout=5)


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
