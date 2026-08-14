#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

"""Image deduplication review for the BIA annales.

Holds the duplicate-image machinery used by gen-csv.py:
- decision cache helpers (in a dedicated diskcache)
- applying canonical decisions to the database and the annales TSV
- a small local FastAPI app to review duplicate image groups
  (transitive closure of similar pairs: A~B and B~C => one group A,B,C)
"""

from __future__ import annotations

import csv
import html
import io

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session, select, col

from PIL import Image, ImageOps

from models import ConsolidatedQuestion, ImageDedupDecision
from check_imgs import SimilarPair, find_duplicate_groups_from_paths
from cache import DECISIONS
from log import SCRIPT_DIR

THE_TSV = SCRIPT_DIR.parent.parent / "site" / "static" / "annales-bia.tsv"
SITE_IMG_DIR = SCRIPT_DIR.parent.parent / "site" / "static" / "img-sujets"

CSV_DELIMITER = "\t"

DEDUP_PREFIX = "image-dedup:"
DEDUP_PORT = 8001
DEDUP_THRESHOLD = 10
DEDUP_SSIM_THRESHOLD = 0.9

Decision = dict[str, object]


def tsv_image_paths() -> list[Path]:
    """Return the image files referenced by the annales TSV.

    Each attachment_link maps to <SITE_IMG_DIR>/<link>.jpeg.
    """
    links: set[str] = set()
    with open(THE_TSV, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=CSV_DELIMITER)
        for row in reader:
            link = row.get("attachment_link", "").strip()
            if link:
                links.add(link)
    paths: list[Path] = []
    for link in sorted(links):
        path = SITE_IMG_DIR / f"{link}.jpeg"
        if path.is_file():
            paths.append(path)
        else:
            print(f"Warning: TSV references image not found: {path.name}")
    return paths


def dedup_cache_key(key: str) -> str:
    return f"{DEDUP_PREFIX}{key}"


def get_decision(key: str) -> Decision | None:
    value = DECISIONS.get(dedup_cache_key(key))
    return value if isinstance(value, dict) else None


def set_decision(key: str, decision: Decision) -> None:
    DECISIONS.set(dedup_cache_key(key), decision)


def clear_decisions() -> None:
    for cache_key in list(DECISIONS):
        if isinstance(cache_key, str) and cache_key.startswith(DEDUP_PREFIX):
            del DECISIONS[cache_key]


def all_decisions() -> list[tuple[str, Decision]]:
    res = []
    for cache_key in list(DECISIONS):
        if not isinstance(cache_key, str) or not cache_key.startswith(DEDUP_PREFIX):
            continue
        value = DECISIONS.get(cache_key)
        if isinstance(value, dict):
            res.append((cache_key[len(DEDUP_PREFIX) :], value))
    return sorted(res)


def update_tsv_attachment_links(updates: dict[str, str]) -> int:
    if not updates:
        return 0
    with open(THE_TSV, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=CSV_DELIMITER)
        rows = list(reader)
        fieldnames: list[str] = list(reader.fieldnames)  # type: ignore[assignment]
    changed = 0
    for row in rows:
        link = row.get("attachment_link")
        if link and link in updates:
            row["attachment_link"] = updates[link]
            changed += 1
    with open(THE_TSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        writer.writerows(rows)
    return changed


def apply_decisions(engine) -> tuple[int, int, int]:
    tsv_updates: dict[str, str] = {}
    applied = 0
    db_rows = 0
    with Session(engine) as session:
        for group_key, value in all_decisions():
            if value.get("applied"):
                continue
            applied += 1
            canonical = value.get("canonical")
            decision_type = value["type"]
            assert isinstance(canonical, str) or canonical is None
            assert isinstance(decision_type, str)
            if decision_type == "canonical" and canonical:
                names = group_key.split("|")
                assert canonical in names, (
                    f"canonical {canonical!r} not in group {group_key!r}"
                )
                for name in names:
                    if name == canonical:
                        continue
                    old_stem = Path(name).stem
                    new_stem = Path(canonical).stem
                    if old_stem != new_stem:
                        tsv_updates[old_stem] = new_stem
                        rows = session.exec(
                            select(ConsolidatedQuestion).where(
                                col(ConsolidatedQuestion.attachment_link) == old_stem
                            )
                        ).all()
                        for row in rows:
                            row.attachment_link = new_stem
                        session.add_all(rows)
                        db_rows += len(rows)
            existing = session.get(ImageDedupDecision, group_key)
            if existing is None:
                session.add(
                    ImageDedupDecision(
                        pair_key=group_key,
                        decision=decision_type,
                        canonical=canonical,
                    )
                )
            else:
                existing.decision = decision_type
                existing.canonical = canonical
                session.add(existing)
            value["applied"] = True
            DECISIONS.set(dedup_cache_key(group_key), value)
        session.commit()
    tsv_changed = update_tsv_attachment_links(tsv_updates)
    print(
        f"Applied {applied} decisions: updated {db_rows} rows in DB, "
        f"{tsv_changed} rows in TSV"
    )
    return applied, db_rows, tsv_changed


def build_attachment_map(engine) -> dict[str, list[dict]]:
    with Session(engine) as session:
        rows = session.exec(select(ConsolidatedQuestion)).all()
    res: dict[str, list[dict]] = {}
    for q in rows:
        if not q.attachment_link:
            continue
        res.setdefault(q.attachment_link, []).append(
            {
                "qid": q.qid,
                "year": q.year,
                "no": q.no,
                "content": q.content_verbatim,
            }
        )
    for lst in res.values():
        lst.sort(key=lambda r: (r["year"], r["no"]))
    return res


def questions_for_image(attachment_map: dict[str, list[dict]], name: str) -> list[dict]:
    return attachment_map.get(Path(name).stem, [])


def render_questions(questions: list[dict]) -> str:
    if not questions:
        return "<p class='muted'>No question references this image.</p>"
    items = []
    for q in questions:
        content = html.escape(q["content"])[:120]
        items.append(
            f"<li><strong>{q['year']} #{q['no'] + 1}</strong> &mdash; {content}</li>"
        )
    return "<ul>" + "".join(items) + "</ul>"


def image_dims(path: Path) -> str:
    try:
        with Image.open(path) as im:
            return f"{im.size[0]} &times; {im.size[1]} px"
    except Exception:
        return ""


@dataclass
class DuplicateGroup:
    key: str  # "|".join(sorted names)
    names: list[str]
    exact: bool  # at least a subset of members is byte-identical

    @property
    def name_set(self) -> set[str]:
        return set(self.names)


class _DSU:
    """Disjoint-set to compute the transitive closure of duplicate edges."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def build_duplicate_groups(
    exact: dict[str, list[str]], pairs: Sequence[SimilarPair]
) -> list[DuplicateGroup]:
    dsu = _DSU()
    for names in exact.values():
        for name in names[1:]:
            dsu.union(names[0], name)
    for pair in pairs:
        dsu.union(pair.a.name, pair.b.name)
    components: dict[str, list[str]] = {}
    for name in dsu.parent:
        root = dsu.find(name)
        components.setdefault(root, []).append(name)
    exact_sets = [set(names) for names in exact.values()]
    groups = []
    for names in components.values():
        names = sorted(names)
        groups.append(
            DuplicateGroup(
                key="|".join(names),
                names=names,
                exact=any(exact_set <= set(names) for exact_set in exact_sets),
            )
        )
    return sorted(groups, key=lambda g: g.key)


DEDUP_CSS = """\
body{font-family:system-ui,sans-serif;margin:1.5rem;color:#1f2937;max-width:1600px}
header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e5e7eb;padding-bottom:.5rem;margin-bottom:1rem}
.toolbar{display:flex;flex-wrap:wrap;gap:.75rem;align-items:flex-end;border:1px solid #d1d5db;border-radius:8px;padding:.75rem;margin-bottom:1rem}
.field{display:flex;flex-direction:column;gap:.2rem}
.field label{font-size:.75rem;color:#6b7280}
.field input{width:8rem;padding:.35rem .5rem;border:1px solid #bbb;border-radius:4px;font-size:.85rem}
.summary{color:#6b7280;font-size:.9rem;margin:0 0 1rem}
.applied{color:#166534;font-weight:600;font-size:.9rem;margin:-.5rem 0 1rem}
.group{border:1px solid #d1d5db;border-radius:8px;margin-bottom:1rem;padding:.75rem}
.group-header{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin-bottom:.5rem}
.imgs{display:flex;gap:.75rem;overflow-x:auto;align-items:flex-start}
.item{min-width:230px;flex:0 0 230px;border:1px solid #e5e7eb;border-radius:6px;padding:.5rem;background:#fafafa}
.item img{max-width:100%;height:auto;border:1px solid #e5e7eb;background:#fff}
.item figure{margin:0 0 .5rem}
.item figcaption{font-size:.75rem;color:#6b7280}
.item ul{font-size:.8rem;padding-left:1.1rem;margin:.25rem 0 0}
.badge{font-size:.75rem;padding:.1rem .45rem;border-radius:999px;border:1px solid;white-space:nowrap}
.badge.pending{background:#f3f4f6;color:#6b7280;border-color:#d1d5db}
.badge.canonical{background:#dcfce7;color:#166534;border-color:#86efac}
.badge.reject{background:#fee2e2;color:#991b1b;border-color:#fca5a5}
.badge.exact{background:#dbeafe;color:#1e40af;border-color:#93c5fd}
.actions{display:flex;gap:.5rem;margin-top:1rem}
button{padding:.6rem .9rem;border-radius:6px;border:1px solid #d1d5db;cursor:pointer;font-size:.9rem}
code{background:#f3f4f6;padding:.1rem .3rem;border-radius:4px;font-size:.8rem}
"""


def render_group_row(state: "ReviewState", group: DuplicateGroup) -> str:
    decision = get_decision(group.key)
    if decision is None:
        badge = "<span class='badge pending'>pending</span>"
    elif decision.get("type") == "canonical":
        badge = (
            "<span class='badge canonical'>keep: "
            f"{html.escape(str(decision['canonical']))}</span>"
        )
    else:
        badge = "<span class='badge reject'>rejected</span>"
    exact_badge = (
        "<span class='badge exact'>byte-identical</span>" if group.exact else ""
    )

    items = []
    for name in group.names:
        questions = questions_for_image(state.attachment_map, name)
        checked = " checked" if decision and decision.get("canonical") == name else ""
        items.append(
            "<div class='item'>"
            f"<figure><img src='/img/{html.escape(name)}' alt='{html.escape(name)}'>"
            f"<figcaption>{html.escape(name)}<br>"
            f"{image_dims(state.name_to_path[name])}</figcaption></figure>"
            f"<label><input type='radio' name='dec:{html.escape(group.key)}' "
            f"value='canonical:{html.escape(name)}'{checked}> Keep this one</label>"
            f"{render_questions(questions)}"
            "</div>"
        )
    reject_checked = " checked" if decision and decision.get("type") == "reject" else ""
    items.append(
        "<div class='item'>"
        "<figure><figcaption>None of these</figcaption></figure>"
        f"<label><input type='radio' name='dec:{html.escape(group.key)}' "
        f"value='reject'{reject_checked}> Reject group (not duplicates)</label>"
        "</div>"
    )

    return (
        "<div class='group'>"
        f"<div class='group-header'><strong>{len(group.names)} images</strong>"
        f"{badge}{exact_badge}<code>{html.escape(group.key)}</code></div>"
        f"<div class='imgs'>{''.join(items)}</div>"
        "</div>"
    )


def render_groups_page(state: "ReviewState") -> str:
    decided = sum(1 for g in state.groups if get_decision(g.key) is not None)
    rows = [render_group_row(state, g) for g in state.groups]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Review duplicate image groups</title>
<style>{DEDUP_CSS}</style>
</head>
<body>
<header>
  <div><strong>Duplicate image review</strong></div>
  <form method="post" action="/reset"><button type="submit">Reset all decisions</button></form>
</header>
<form method="get" action="/">
  <div class="toolbar">
    <div class="field"><label>Hamming threshold (0&ndash;64, lower = stricter)</label><input type="number" name="threshold" min="0" max="64" value="{state.threshold}"></div>
    <div class="field"><label>SSIM threshold (0&ndash;1, higher = stricter)</label><input type="number" name="ssim" min="0" max="1" step="0.05" value="{state.ssim_threshold}"></div>
    <div class="field"><label>&nbsp;</label><button type="submit">Rescan</button></div>
  </div>
</form>
<p class="summary">{len(state.groups)} groups &mdash; {decided} decided, {len(state.groups) - decided} pending (threshold: hamming &le; {state.threshold}, ssim &ge; {state.ssim_threshold}).</p>
{f'<p class="applied">{html.escape(state.last_apply)}</p>' if state.last_apply else ""}
<form method="post" action="/decision">
  {"".join(rows)}
  <div class="actions">
    <button type="submit" name="save" value="1">Save all decisions</button>
    <button type="submit" name="apply" value="1">Apply decisions to database + TSV</button>
  </div>
</form>
</body>
</html>"""


def convert_to_png(path: Path) -> bytes:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


class ReviewState:
    engine: object
    attachment_map: dict[str, list[dict]]
    name_to_path: dict[str, Path]
    converted: dict[str, bytes]
    threshold: int
    ssim_threshold: float
    groups: list[DuplicateGroup]
    last_scan: tuple[int, float] | None
    last_apply: str | None

    def __init__(
        self,
        engine,
        attachment_map: dict[str, list[dict]],
        threshold: int,
        ssim_threshold: float,
    ) -> None:
        self.engine = engine
        self.attachment_map = attachment_map
        self.name_to_path = {}
        self.converted = {}
        self.threshold = threshold
        self.ssim_threshold = ssim_threshold
        self.groups = []
        self.last_scan = None
        self.last_apply = None

    def rescan(
        self, threshold: int, ssim_threshold: float, verbose: bool = False
    ) -> None:
        if (threshold, ssim_threshold) == self.last_scan:
            return
        self.threshold = threshold
        self.ssim_threshold = ssim_threshold
        print(
            f"Scanning images for duplicates (hamming<={threshold}, "
            f"ssim>={ssim_threshold})..."
        )
        paths = tsv_image_paths()
        exact, pairs = find_duplicate_groups_from_paths(
            paths, threshold, ssim_threshold, verbose=verbose
        )
        if exact:
            print("=== Exact duplicates (identical bytes) ===")
            for names in exact.values():
                print("  " + " == ".join(names))
        name_to_path = {path.name: path for path in paths}
        self.groups = build_duplicate_groups(exact, pairs)
        self.name_to_path = {
            name: name_to_path[name] for group in self.groups for name in group.names
        }
        self.last_scan = (threshold, ssim_threshold)
        self.last_apply = None
        pending = sum(1 for g in self.groups if get_decision(g.key) is None)
        print(f"{len(self.groups)} duplicate groups found, {pending} pending review")


def back_url(state: "ReviewState") -> str:
    return f"/?threshold={state.threshold}&ssim={state.ssim_threshold}"


def create_dedup_app(state: ReviewState) -> FastAPI:
    app = FastAPI(title="Duplicate image review")

    @app.get("/", response_class=HTMLResponse)
    def index(
        threshold: int = Query(default=DEDUP_THRESHOLD),
        ssim: float = Query(default=DEDUP_SSIM_THRESHOLD),
    ) -> str:
        state.rescan(threshold, ssim)
        return render_groups_page(state)

    @app.get("/img/{name}")
    def serve_image(name: str) -> Response:
        path = state.name_to_path.get(name)
        if path is None or not path.is_file():
            return Response("Not found", status_code=404, media_type="text/plain")
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg"}:
            return Response(
                path.read_bytes(),
                media_type=f"image/{'png' if suffix == '.png' else 'jpeg'}",
            )
        converted = state.converted.get(name)
        if converted is None:
            converted = convert_to_png(path)
            state.converted[name] = converted
        return Response(converted, media_type="image/png")

    @app.post("/decision")
    async def decision(request: Request) -> RedirectResponse:
        form = await request.form()
        for field_name, value in form.multi_items():
            if not field_name.startswith("dec:"):
                continue
            key = field_name[len("dec:") :]
            val = str(value)
            if val.startswith("canonical:"):
                set_decision(
                    key, {"type": "canonical", "canonical": val.split(":", 1)[1]}
                )
            elif val == "reject":
                set_decision(key, {"type": "reject"})
        if form.get("apply"):
            _apply(state)
        return RedirectResponse(back_url(state), status_code=303)

    @app.post("/reset")
    def reset() -> RedirectResponse:
        clear_decisions()
        return RedirectResponse(back_url(state), status_code=303)

    @app.post("/apply")
    def apply() -> RedirectResponse:
        _apply(state)
        return RedirectResponse(back_url(state), status_code=303)

    return app


def _apply(state: "ReviewState") -> None:
    applied, db_rows, tsv_changed = apply_decisions(state.engine)
    state.last_apply = (
        f"Applied {applied} decision(s): {db_rows} DB row(s) and "
        f"{tsv_changed} TSV row(s) updated."
    )


def review_image_duplicates(engine, args) -> None:
    attachment_map = build_attachment_map(engine)
    state = ReviewState(
        engine=engine,
        attachment_map=attachment_map,
        threshold=args.threshold,
        ssim_threshold=args.ssim_threshold,
    )
    state.rescan(args.threshold, args.ssim_threshold, verbose=True)
    app = create_dedup_app(state)
    print(f"Dedup review app running at http://localhost:{args.port}")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port)
