#!/usr/bin/env python3
"""
PNG to JPEG Compression Tuning Server
A single-file Python web application to tune and batch-process PNG-to-JPEG compression using ImageMagick (`magick`).
"""

import os
import sys
import json
import shutil
import pathlib
import tempfile
import threading
import subprocess
import webbrowser
from urllib.parse import parse_qs, urlparse
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler

DEFAULT_PORT = 8000


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


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PNG to JPEG Magick Tuner</title>
  <style>
    :root {
      --bg-color: #0f172a;
      --panel-bg: #1e293b;
      --panel-border: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-color: #3b82f6;
      --accent-hover: #2563eb;
      --success-color: #22c55e;
      --warning-color: #f59e0b;
      --danger-color: #ef4444;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    header {
      background-color: var(--panel-bg);
      border-bottom: 1px solid var(--panel-border);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    h1 {
      font-size: 1.2rem;
      font-weight: 600;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .toolbar {
      background-color: var(--panel-bg);
      border-bottom: 1px solid var(--panel-border);
      padding: 14px 20px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      align-items: end;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .form-group label {
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--text-muted);
    }

    .form-group label .required {
      color: var(--danger-color);
    }

    .input-with-btn {
      display: flex;
      gap: 6px;
    }

    .input-with-btn input[type="text"] {
      flex: 1;
    }

    input[type="text"],
    input[type="number"],
    select {
      background-color: var(--bg-color);
      border: 1px solid var(--panel-border);
      color: var(--text-main);
      padding: 7px 10px;
      border-radius: 6px;
      font-size: 0.88rem;
      outline: none;
      transition: border-color 0.2s;
    }

    input[type="text"]:focus,
    input[type="number"]:focus,
    select:focus {
      border-color: var(--accent-color);
    }

    .quality-control {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .quality-control input[type="range"] {
      flex: 1;
      accent-color: var(--accent-color);
    }

    .quality-control input[type="number"] {
      width: 60px;
      text-align: center;
    }

    .btn-group {
      display: flex;
      gap: 8px;
    }

    button {
      background-color: var(--accent-color);
      color: white;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.2s, opacity 0.2s;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    button:hover {
      background-color: var(--accent-hover);
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    button.btn-secondary {
      background-color: #334155;
      color: #f8fafc;
    }

    button.btn-secondary:hover {
      background-color: #475569;
    }

    button.btn-success {
      background-color: var(--success-color);
    }
    button.btn-success:hover {
      background-color: #16a34a;
    }

    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      background-color: #090d16;
      overflow: hidden;
      padding: 16px;
    }

    .image-container {
      position: relative;
      max-width: 100%;
      max-height: calc(100vh - 240px);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .image-container img {
      max-width: 100%;
      max-height: calc(100vh - 240px);
      object-fit: contain;
      border-radius: 6px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }

    .status-badge {
      position: absolute;
      top: 12px;
      left: 12px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
      pointer-events: none;
      user-select: none;
      z-index: 10;
    }

    .status-badge.original {
      background-color: var(--warning-color);
      color: #000;
    }

    .status-badge.compressed {
      background-color: var(--accent-color);
      color: #fff;
    }

    .stats-bar {
      margin-top: 14px;
      display: flex;
      gap: 20px;
      background-color: var(--panel-bg);
      border: 1px solid var(--panel-border);
      padding: 8px 18px;
      border-radius: 30px;
      font-size: 0.85rem;
      align-items: center;
    }

    .stat-item {
      display: flex;
      gap: 6px;
    }
    .stat-label {
      color: var(--text-muted);
    }
    .stat-value {
      font-weight: 600;
    }
    .savings-pill {
      background-color: rgba(34, 197, 94, 0.2);
      color: var(--success-color);
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 700;
    }

    .nav-overlay {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      background-color: rgba(30, 41, 59, 0.7);
      color: white;
      border: 1px solid var(--panel-border);
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.2rem;
      user-select: none;
      transition: background-color 0.2s;
      z-index: 5;
    }

    .nav-overlay:hover {
      background-color: var(--accent-color);
    }

    .nav-overlay.prev { left: 20px; }
    .nav-overlay.next { right: 20px; }

    footer {
      background-color: var(--panel-bg);
      border-top: 1px solid var(--panel-border);
      padding: 8px 20px;
      font-size: 0.78rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .shortcuts-guide {
      display: flex;
      gap: 16px;
    }

    .kbd {
      background-color: var(--bg-color);
      border: 1px solid var(--panel-border);
      border-radius: 4px;
      padding: 1px 6px;
      font-family: monospace;
      color: var(--text-main);
    }

    .alert {
      position: fixed;
      bottom: 50px;
      left: 50%;
      transform: translateX(-50%);
      background-color: var(--danger-color);
      color: white;
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 0.9rem;
      box-shadow: 0 4px 14px rgba(0,0,0,0.4);
      display: none;
      z-index: 100;
      max-width: 80%;
      text-align: center;
    }

    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.2);
      border-top: 3px solid var(--accent-color);
      border-radius: 50%;
      width: 24px;
      height: 24px;
      animation: spin 0.8s linear infinite;
      display: none;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>

  <header>
    <h1><span>🖼️</span> PNG to JPEG Magick Compression Tuner</h1>
    <div id="file-counter" style="color: var(--text-muted); font-size: 0.9rem;">No folder loaded</div>
  </header>

  <div class="toolbar">
    <div class="form-group" style="grid-column: span 2;">
      <label for="input-dir">Input Directory</label>
      <div class="input-with-btn">
        <input type="text" id="input-dir" placeholder="/path/to/png/pics">
        <button class="btn-secondary" onclick="selectDir('input-dir')" title="Open System Finder / File Manager">📂 Browse...</button>
      </div>
    </div>

    <div class="form-group" style="grid-column: span 2;">
      <label for="output-dir">Output Directory <span class="required">*</span></label>
      <div class="input-with-btn">
        <input type="text" id="output-dir" placeholder="/path/to/output/jpegs">
        <button class="btn-secondary" onclick="selectDir('output-dir')" title="Open System Finder / File Manager">📂 Browse...</button>
      </div>
    </div>

    <div class="form-group">
      <label for="suffix">Output Suffix</label>
      <input type="text" id="suffix" value="_minified.jpeg">
    </div>

    <div class="form-group">
      <label for="sampling-factor">Sampling Factor (-sampling-factor)</label>
      <select id="sampling-factor">
        <option value="4:4:4" selected>4:4:4 (High Quality)</option>
        <option value="4:2:2">4:2:2 (Medium)</option>
        <option value="4:2:0">4:2:0 (Standard)</option>
        <option value="4:0:0">4:0:0 (Grayscale)</option>
      </select>
    </div>

    <div class="form-group">
      <label for="quality">Quality (-quality 1-100)</label>
      <div class="quality-control">
        <input type="range" id="quality-slider" min="1" max="100" value="10">
        <input type="number" id="quality" min="1" max="100" value="10">
      </div>
    </div>

    <div class="form-group">
      <label for="quality-step">Quality Key Step</label>
      <input type="number" id="quality-step" min="1" max="50" value="5">
    </div>

    <div class="btn-group" style="grid-column: span 2;">
      <button id="btn-load" onclick="loadImages()">Load Folder</button>
      <button id="btn-batch" class="btn-success" onclick="runBatch()" disabled>⚡ Batch Compress All</button>
      <div class="spinner" id="spinner"></div>
    </div>
  </div>

  <div class="main-content">
    <div id="status-badge" class="status-badge compressed">COMPRESSED JPEG</div>

    <button class="nav-overlay prev" onclick="prevImage()" title="Previous Image (Left Arrow)">&#10094;</button>
    
    <div class="image-container">
      <img id="preview-img" alt="Select a folder to begin preview" style="display: none;">
      <div id="empty-state" style="color: var(--text-muted); text-align: center;">
        <p style="font-size: 1.1rem; margin-bottom: 8px;">Enter input folder path or click <strong>Browse...</strong> to load images</p>
        <p style="font-size: 0.85rem;">Magick command: <code>magick "$input" -sampling-factor 4:4:4 -quality 10 "$output"</code></p>
      </div>
    </div>

    <button class="nav-overlay next" onclick="nextImage()" title="Next Image (Right Arrow)">&#10095;</button>

    <div class="stats-bar" id="stats-bar" style="visibility: hidden;">
      <div class="stat-item">
        <span class="stat-label">File:</span>
        <span class="stat-value" id="stat-filename">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Original PNG:</span>
        <span class="stat-value" id="stat-orig-size">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Compressed JPEG:</span>
        <span class="stat-value" id="stat-comp-size">-</span>
      </div>
      <div class="stat-item">
        <span class="savings-pill" id="stat-savings">-</span>
      </div>
    </div>
  </div>

  <footer>
    <div class="shortcuts-guide">
      <span><span class="kbd">Hold Space</span> View Original</span>
      <span><span class="kbd">Release Space</span> View Compressed</span>
      <span><span class="kbd">&uparrow;</span> / <span class="kbd">&downarrow;</span> Quality +/- Step</span>
      <span><span class="kbd">&leftarrow;</span> / <span class="kbd">&rightarrow;</span> Prev / Next Image</span>
    </div>
    <div>Magick Web Tuner</div>
  </footer>

  <div id="alert-banner" class="alert"></div>

  <script>
    let imagesList = [];
    let currentIndex = 0;
    let spacePressed = false;
    let currentPreviewUrl = null;
    let currentOriginalUrl = null;

    // Elements
    const inputDirEl = document.getElementById('input-dir');
    const outputDirEl = document.getElementById('output-dir');
    const suffixEl = document.getElementById('suffix');
    const samplingEl = document.getElementById('sampling-factor');
    const qualityNumEl = document.getElementById('quality');
    const qualitySliderEl = document.getElementById('quality-slider');
    const qualityStepEl = document.getElementById('quality-step');

    const previewImg = document.getElementById('preview-img');
    const emptyState = document.getElementById('empty-state');
    const statusBadge = document.getElementById('status-badge');
    const fileCounter = document.getElementById('file-counter');
    const alertBanner = document.getElementById('alert-banner');
    const spinner = document.getElementById('spinner');
    const statsBar = document.getElementById('stats-bar');
    const btnBatch = document.getElementById('btn-batch');

    // Sync Quality Slider and Number
    qualitySliderEl.addEventListener('input', (e) => {
      qualityNumEl.value = e.target.value;
      updatePreview();
    });

    qualityNumEl.addEventListener('change', (e) => {
      let val = parseInt(e.target.value, 10);
      if (isNaN(val)) val = 10;
      val = Math.max(1, Math.min(100, val));
      qualityNumEl.value = val;
      qualitySliderEl.value = val;
      updatePreview();
    });

    samplingEl.addEventListener('change', updatePreview);

    function showAlert(msg) {
      alertBanner.textContent = msg;
      alertBanner.style.display = 'block';
      setTimeout(() => {
        alertBanner.style.display = 'none';
      }, 5000);
    }

    function formatBytes(bytes) {
      if (bytes === 0 || !bytes) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async function selectDir(targetId) {
      spinner.style.display = 'inline-block';
      try {
        const title = targetId === 'input-dir' ? 'Select Input Directory containing PNGs' : 'Select Mandatory Output Directory';
        const res = await fetch('/api/select-dir', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: title })
        });
        const data = await res.json();
        if (res.ok && data.path) {
          document.getElementById(targetId).value = data.path;
          if (targetId === 'input-dir') {
            loadImages();
          }
        }
      } catch (err) {
        showAlert("Failed to open system finder: " + err.message);
      } finally {
        spinner.style.display = 'none';
      }
    }

    async function loadImages() {
      const dir = inputDirEl.value.trim();
      if (!dir) {
        showAlert("Please enter an input directory path or click Browse.");
        return;
      }

      spinner.style.display = 'inline-block';
      try {
        const res = await fetch(`/api/images?dir=${encodeURIComponent(dir)}`);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || "Failed to load directory");
        }

        imagesList = data.images;
        currentIndex = 0;
        if (imagesList.length === 0) {
          showAlert("No PNG images found in the specified directory.");
          previewImg.style.display = 'none';
          emptyState.style.display = 'block';
          fileCounter.textContent = "0 images found";
          btnBatch.disabled = true;
          statsBar.style.visibility = 'hidden';
        } else {
          fileCounter.textContent = `${imagesList.length} PNG images found`;
          btnBatch.disabled = false;
          emptyState.style.display = 'none';
          previewImg.style.display = 'block';
          updatePreview();
        }
      } catch (err) {
        showAlert(err.message);
      } finally {
        spinner.style.display = 'none';
      }
    }

    async function updatePreview() {
      if (imagesList.length === 0) return;

      const item = imagesList[currentIndex];
      const path = item.path;
      const q = qualityNumEl.value;
      const sf = samplingEl.value;

      fileCounter.textContent = `Image ${currentIndex + 1} of ${imagesList.length}: ${item.name}`;
      document.getElementById('stat-filename').textContent = item.name;

      currentOriginalUrl = `/api/original?path=${encodeURIComponent(path)}`;

      spinner.style.display = 'inline-block';
      try {
        const previewApiUrl = `/api/preview?path=${encodeURIComponent(path)}&quality=${q}&sampling_factor=${encodeURIComponent(sf)}`;
        const res = await fetch(previewApiUrl);
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.error || "Magick conversion failed");
        }

        const origSize = parseInt(res.headers.get('X-Original-Size') || item.size, 10);
        const compSize = parseInt(res.headers.get('X-Compressed-Size') || '0', 10);

        document.getElementById('stat-orig-size').textContent = formatBytes(origSize);
        document.getElementById('stat-comp-size').textContent = formatBytes(compSize);

        const savings = origSize > 0 ? (((origSize - compSize) / origSize) * 100).toFixed(1) : 0;
        const savingsEl = document.getElementById('stat-savings');
        savingsEl.textContent = `${savings}% smaller`;

        const blob = await res.blob();
        if (currentPreviewUrl) {
          URL.revokeObjectURL(currentPreviewUrl);
        }
        currentPreviewUrl = URL.createObjectURL(blob);

        if (spacePressed) {
          previewImg.src = currentOriginalUrl;
          statusBadge.textContent = "ORIGINAL PNG";
          statusBadge.className = "status-badge original";
        } else {
          previewImg.src = currentPreviewUrl;
          statusBadge.textContent = `COMPRESSED JPEG (Q: ${q})`;
          statusBadge.className = "status-badge compressed";
        }
        statsBar.style.visibility = 'visible';
      } catch (err) {
        showAlert(err.message);
      } finally {
        spinner.style.display = 'none';
      }
    }

    function prevImage() {
      if (imagesList.length === 0) return;
      currentIndex = (currentIndex - 1 + imagesList.length) % imagesList.length;
      updatePreview();
    }

    function nextImage() {
      if (imagesList.length === 0) return;
      currentIndex = (currentIndex + 1) % imagesList.length;
      updatePreview();
    }

    function adjustQuality(delta) {
      let currentQ = parseInt(qualityNumEl.value, 10) || 10;
      let newQ = Math.max(1, Math.min(100, currentQ + delta));
      qualityNumEl.value = newQ;
      qualitySliderEl.value = newQ;
      updatePreview();
    }

    async function runBatch() {
      const inputDir = inputDirEl.value.trim();
      const outputDir = outputDirEl.value.trim();
      const suffix = suffixEl.value.trim();
      const q = parseInt(qualityNumEl.value, 10);
      const sf = samplingEl.value;

      if (!outputDir) {
        showAlert("Error: Output directory is mandatory for batch processing.");
        outputDirEl.focus();
        return;
      }

      if (!inputDir) {
        showAlert("Error: Input directory is missing.");
        return;
      }

      spinner.style.display = 'inline-block';
      btnBatch.disabled = true;

      try {
        const res = await fetch('/api/batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            input_dir: inputDir,
            output_dir: outputDir,
            suffix: suffix,
            quality: q,
            sampling_factor: sf
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || "Batch processing failed.");
        }

        showAlert(`Success! Batch compressed ${data.processed} images. Saved ${data.savings_percent}% space overall.`);
      } catch (err) {
        showAlert(err.message);
      } finally {
        spinner.style.display = 'none';
        btnBatch.disabled = false;
      }
    }

    // Keyboard Shortcuts Logic
    window.addEventListener('keydown', (e) => {
      // Ignore shortcut keys if user is typing into text or number inputs
      const tag = document.activeElement ? document.activeElement.tagName : '';
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(tag)) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        if (!spacePressed) {
          spacePressed = true;
          if (currentOriginalUrl) {
            previewImg.src = currentOriginalUrl;
            statusBadge.textContent = "ORIGINAL PNG";
            statusBadge.className = "status-badge original";
          }
        }
      } else if (e.code === 'ArrowUp') {
        e.preventDefault();
        const step = parseInt(qualityStepEl.value, 10) || 5;
        adjustQuality(step);
      } else if (e.code === 'ArrowDown') {
        e.preventDefault();
        const step = parseInt(qualityStepEl.value, 10) || 5;
        adjustQuality(-step);
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        prevImage();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        nextImage();
      }
    });

    window.addEventListener('keyup', (e) => {
      const tag = document.activeElement ? document.activeElement.tagName : '';
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(tag) && e.code !== 'Space') {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        spacePressed = false;
        if (currentPreviewUrl) {
          previewImg.src = currentPreviewUrl;
          const q = qualityNumEl.value;
          statusBadge.textContent = `COMPRESSED JPEG (Q: ${q})`;
          statusBadge.className = "status-badge compressed";
        }
      }
    });

    window.addEventListener('blur', () => {
      if (spacePressed) {
        spacePressed = false;
        if (currentPreviewUrl) {
          previewImg.src = currentPreviewUrl;
          const q = qualityNumEl.value;
          statusBadge.textContent = `COMPRESSED JPEG (Q: ${q})`;
          statusBadge.className = "status-badge compressed";
        }
      }
    });
  </script>
</body>
</html>
"""


class MagickTunerHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status=status)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/" or path == "/index.html":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/images":
            dirs = query.get("dir", [""])
            dir_path_str = dirs[0]
            if not dir_path_str:
                self.send_error_json("Directory path is required.")
                return

            dir_path = pathlib.Path(dir_path_str).expanduser().resolve()
            if not dir_path.is_dir():
                self.send_error_json(
                    f"Directory non-existent or invalid: {dir_path_str}"
                )
                return

            images = []
            for item in sorted(dir_path.iterdir()):
                if item.is_file() and item.suffix.lower() == ".png":
                    images.append(
                        {
                            "name": item.name,
                            "path": str(item),
                            "size": item.stat().st_size,
                        }
                    )

            self.send_json({"images": images})
            return

        if path == "/api/original":
            paths = query.get("path", [""])
            img_path_str = paths[0]
            if not img_path_str:
                self.send_error_json("Path is required.")
                return

            img_path = pathlib.Path(img_path_str)
            if not img_path.is_file():
                self.send_error_json(f"File not found: {img_path_str}", status=404)
                return

            try:
                with open(img_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error_json(f"Error reading file: {e}", status=500)
            return

        if path == "/api/preview":
            paths = query.get("path", [""])
            qualities = query.get("quality", ["10"])
            samplings = query.get("sampling_factor", ["4:4:4"])

            img_path_str = paths[0]
            quality = qualities[0]
            sampling_factor = samplings[0]

            if not img_path_str:
                self.send_error_json("Image path is required.")
                return

            img_path = pathlib.Path(img_path_str)
            if not img_path.is_file():
                self.send_error_json(
                    f"Image file not found: {img_path_str}", status=404
                )
                return

            orig_size = img_path.stat().st_size

            with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as tmp_file:
                tmp_output = tmp_file.name

            try:
                # Execution pattern: magick "$input" -sampling-factor 4:4:4 -quality 10 "$output"
                cmd = [
                    "magick",
                    str(img_path),
                    "-sampling-factor",
                    sampling_factor,
                    "-quality",
                    str(quality),
                    tmp_output,
                ]

                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    err_msg = (
                        res.stderr.strip()
                        or f"magick exited with code {res.returncode}"
                    )
                    self.send_error_json(f"Magick error: {err_msg}", status=500)
                    return

                comp_size = os.path.getsize(tmp_output)
                with open(tmp_output, "rb") as f:
                    jpeg_bytes = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg_bytes)))
                self.send_header("X-Original-Size", str(orig_size))
                self.send_header("X-Compressed-Size", str(comp_size))
                self.send_header(
                    "Access-Control-Expose-Headers",
                    "X-Original-Size, X-Compressed-Size",
                )
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(jpeg_bytes)

            except FileNotFoundError:
                self.send_error_json(
                    "Command 'magick' not found. Please ensure ImageMagick is installed and in your PATH.",
                    status=500,
                )
            except Exception as e:
                self.send_error_json(f"Unexpected error: {e}", status=500)
            finally:
                if os.path.exists(tmp_output):
                    try:
                        os.remove(tmp_output)
                    except OSError:
                        pass
            return

        self.send_error_json("Endpoint not found", status=404)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/select-dir":
            content_length = int(self.headers.get("Content-Length", 0))
            payload = {}
            if content_length > 0:
                try:
                    post_data = self.rfile.read(content_length)
                    payload = json.loads(post_data.decode("utf-8"))
                except Exception:
                    pass
            title = payload.get("title", "Select Directory")
            folder = select_directory(title=title)
            if folder:
                self.send_json({"path": folder})
            else:
                self.send_json({"path": None, "cancelled": True})
            return

        if path == "/api/batch":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_error_json("Empty request payload.")
                return

            try:
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self.send_error_json(f"Invalid JSON payload: {e}")
                return

            input_dir_str = payload.get("input_dir", "").strip()
            output_dir_str = payload.get("output_dir", "").strip()
            suffix = payload.get("suffix", "_minified.jpeg")
            quality = str(payload.get("quality", 10))
            sampling_factor = payload.get("sampling_factor", "4:4:4")

            if not output_dir_str:
                self.send_error_json("Output directory is mandatory.")
                return

            if not input_dir_str:
                self.send_error_json("Input directory is required.")
                return

            input_dir = pathlib.Path(input_dir_str).expanduser().resolve()
            output_dir = pathlib.Path(output_dir_str).expanduser().resolve()

            if not input_dir.is_dir():
                self.send_error_json(f"Input directory does not exist: {input_dir_str}")
                return

            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.send_error_json(f"Failed to create output directory: {e}")
                return

            img_files = [
                f
                for f in sorted(input_dir.iterdir())
                if f.is_file()
                and f.suffix.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif")
                )
            ]
            if not img_files:
                self.send_error_json("No PNG images found in input directory.")
                return

            processed_count = 0
            total_orig_bytes = 0
            total_comp_bytes = 0

            for img_file in img_files:
                stem = img_file.stem
                out_filename = stem + suffix
                out_path = output_dir / out_filename

                cmd = [
                    "magick",
                    str(img_file),
                    "-sampling-factor",
                    sampling_factor,
                    "-quality",
                    quality,
                    str(out_path),
                ]

                try:
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode != 0:
                        err_msg = res.stderr.strip() or f"code {res.returncode}"
                        self.send_error_json(
                            f"Magick error on {img_file.name}: {err_msg}", status=500
                        )
                        return

                    total_orig_bytes += img_file.stat().st_size
                    total_comp_bytes += out_path.stat().st_size
                    processed_count += 1
                except FileNotFoundError:
                    self.send_error_json("Command 'magick' not found.", status=500)
                    return
                except Exception as e:
                    self.send_error_json(
                        f"Error processing {img_file.name}: {e}", status=500
                    )
                    return

            savings_pct = 0.0
            if total_orig_bytes > 0:
                savings_pct = round(
                    ((total_orig_bytes - total_comp_bytes) / total_orig_bytes) * 100, 1
                )

            self.send_json(
                {
                    "processed": processed_count,
                    "total_orig_bytes": total_orig_bytes,
                    "total_comp_bytes": total_comp_bytes,
                    "savings_percent": savings_pct,
                }
            )
            return

        self.send_error_json("Endpoint not found", status=404)


def open_browser(port):
    """Opens the web browser pointing to localhost."""
    webbrowser.open(f"http://localhost:{port}")


def run_server(port=DEFAULT_PORT):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, MagickTunerHandler)
    print(f"🚀 PNG to JPEG Magick Tuner running on http://localhost:{port}")

    # Automatically open in browser upon launch
    threading.Timer(0.5, open_browser, args=(port,)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
