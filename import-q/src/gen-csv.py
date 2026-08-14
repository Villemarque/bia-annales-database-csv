#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import argparse
import csv
import html
import io

import Levenshtein

from copy import deepcopy
from argparse import RawTextHelpFormatter
from pathlib import Path
from typing import Tuple, Sequence, Iterable

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session, select, col
from sqlalchemy import and_

from PIL import Image, ImageOps

from models import (
    AfQuestion,
    AnnaleQuestion,
    PdfQuestion,
    create_engine,
    AnnaleToAfMapping,
    gen_unique_id,
    ConsolidatedQuestion,
    ImageDedupDecision,
)
from check_imgs import (
    ANNALES_IMG_DIR,
    SimilarPair,
    Fingerprint,
    find_duplicate_groups,
    pair_key,
)
from log import SCRIPT_DIR, log
from cache import DECISIONS

#############
# Constants #
#############

THE_TSV = SCRIPT_DIR.parent.parent / "site" / "static" / "annales-bia.tsv"
THE_CSV = THE_TSV

DEDUP_PREFIX = "image-dedup:"
DEDUP_PORT = 8001
DEDUP_THRESHOLD = 10
DEDUP_SSIM_THRESHOLD = 0.9

########
# Logs #
########

###########
# Classes #
###########


def gen_consolidated(engine):
    with Session(engine) as session:
        statement = (
            select(AnnaleQuestion, AfQuestion)
            .outerjoin(
                AnnaleToAfMapping,
                col(AnnaleQuestion.question_id)
                == col(AnnaleToAfMapping.annale_question_id),
            )
            .outerjoin(
                AfQuestion,
                and_(
                    col(AnnaleToAfMapping.af_question_id)
                    == col(AfQuestion.question_id),
                    col(AnnaleToAfMapping.is_same).is_(True),
                ),
            )
        )
        results = sorted(
            session.exec(statement).all(), key=lambda pair: annale_label_to_ord(pair[0])
        )
        print("Total consolidated questions to generate:", len(results))
    year = None
    i = 0
    with Session(engine) as session:
        for annale, af in results:
            if year is None:
                year = annale.year
            if year != annale.year:
                year = annale.year
                i = 0

            fixed = None
            if af is not None:
                leven = Levenshtein.distance(af.clean_content(), annale.clean_content())
                if leven >= 5 or len(annale.content) >= (len(af.content) + 5):
                    fixed = af.content

            subject_no, question_no = from_label_subject_and_no(annale.question_number)
            c = ConsolidatedQuestion(
                qid=gen_unique_id(),
                year=annale.year,
                subject=subject_no,
                no_subject=question_no,
                no=i,
                content_verbatim=annale.content,
                content_fixed=fixed,
                choice_a=annale.choice_a,
                choice_b=annale.choice_b,
                choice_c=annale.choice_c,
                choice_d=annale.choice_d,
                answer=annale.answer,
                chapter=af.chapter if af is not None else None,
                attachment_link=(
                    af.attachment_link if af is not None else annale.attachment_link
                ),
                mixed_choices=af.mixed_choices if af is not None else None,
            )
            session.add(c)
            i += 1
        session.commit()


def gen_consolidated_pdf(engine):
    with Session(engine) as session:
        statement = select(PdfQuestion)
        pdf_questions = session.exec(statement).all()
        results = sorted(pdf_questions, key=annale_label_to_ord)
        print("Total PDF questions retrieved:", len(results))

    generated_questions = []
    current_year = None
    i = 0
    for pdf in results:
        if current_year is None or current_year != pdf.year:
            current_year = pdf.year
            i = 0

        subject_no, question_no = from_label_subject_and_no(pdf.question_number)
        c = ConsolidatedQuestion(
            qid=gen_unique_id(),
            year=pdf.year,
            subject=subject_no,
            no_subject=question_no,
            no=i,
            content_verbatim=pdf.content,
            content_fixed=None,
            choice_a=pdf.choice_a,
            choice_b=pdf.choice_b,
            choice_c=pdf.choice_c,
            choice_d=pdf.choice_d,
            answer=pdf.answer if pdf.answer is not None else 0,
            chapter=None,
            attachment_link=None,
            mixed_choices=None,
        )
        generated_questions.append(c)
        i += 1

    with Session(engine) as session:
        existing = session.exec(select(ConsolidatedQuestion)).all()
        existing_year_no = {(cq.year, cq.no) for cq in existing}

        added_count = 0
        for c in generated_questions:
            key = (c.year, c.no)
            if key in existing_year_no:
                continue

            session.add(c)
            existing_year_no.add(key)
            added_count += 1

        session.commit()
        print(f"Added {added_count} new consolidated questions from PDF.")


def annale_label_to_ord(annale) -> Tuple[int, int, int]:
    year = annale.year
    import re

    match = re.match(r"(.)\.(\d+)", annale.question_number)
    assert match is not None, f"Bad question number format: {annale.question_number}"
    try:
        subject_no = int(match.group(1))
    except ValueError:
        assert match.group(1) == "F"
        subject_no = 6  # English is subject 6
    question_no = int(match.group(2))
    return (year, subject_no, question_no)


CSV_DELIMITER = "\t"


def from_label_subject_and_no(label: str) -> Tuple[int, int]:
    import re

    match = re.match(r"(.)\.(\d+)", label)
    assert match is not None, f"Bad question number format: {label}"
    try:
        subject_no = int(match.group(1)) - 1  # we wanto 0-based
    except ValueError:
        assert match.group(1) == "F"
        subject_no = 5
    question_no = int(match.group(2)) - 1  # we want 0-based
    return (subject_no, question_no)


def open_csv_with_fieldnames() -> Tuple[list[str], Iterable[any]]:
    with open(THE_CSV, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=CSV_DELIMITER)
        rows = list(reader)

    old_fields: list[str] = list(reader.fieldnames)  # type: ignore
    return old_fields, rows


def cap_bool(v):
    # Only convert actual booleans (not truthy values like 1, "yes", etc.)
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return v


def write_csv(fieldnames, rows) -> None:
    with open(THE_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        for row in rows:
            writer.writerows({k: cap_bool(v) for k, v in row.items()} for row in rows)


def add_subject_to_csv(_):
    old_fields, rows = open_csv_with_fieldnames()
    assert old_fields
    assert "subject" not in old_fields, "subject column already exists"
    new_fields = deepcopy(old_fields)
    new_fields.remove("label")
    new_fields.insert(2, "subject")
    new_fields.insert(3, "no_subject")
    for row in rows:
        subject_no, question_no = from_label_subject_and_no(row["label"])
        row["subject"] = subject_no
        row["no_subject"] = question_no
        del row["label"]
    write_csv(new_fields, rows)


CHAPTERS = {
    "1.1.": 0,  # Les aéronefs
    "1.2.": 1,  # Instrumentation
    "1.3.": 2,  # Moteurs
    "2.1.": 3,  # la sustentation de l'aile
    "2.2.": 4,  # Le vol stabilisé
    "2.3.": 5,  # L'aérostation et le vol spatial
    "3.1.": 6,  # L'atmosphère
    "3.2.": 7,  # Les masses d'air et les fronts
    "3.3.": 8,  # Les nuages
    "3.4.": 9,  # Les vents
    "3.5.": 10,  # Les phénomènes dangereux
    "3.6.": 11,  # L'information météo
    "4.1.": 12,  # Réglementation
    "4.2.": 13,  # SV & FH
    "4.3.": 14,  # Navigation
}


def change_chapters_to_number_csv(_):
    old_fields, rows = open_csv_with_fieldnames()
    new_fields = deepcopy(old_fields)
    for row in rows:
        if row["chapter"] != "":
            if row["chapter"] in ["5.", "6."]:  # We do not split those into chapters
                row["chapter"] = None
            else:
                row["chapter"] = CHAPTERS[row["chapter"]]
    write_csv(new_fields, rows)


def export_csv(engine):
    with Session(engine) as session:
        statement = select(ConsolidatedQuestion)
        results = sorted(session.exec(statement).all(), key=lambda q: (q.year, q.no))
    dicts = [r.model_dump() for r in results]
    log.info(f"Exporting {len(dicts)} consolidated questions to CSV")
    # specifying manually to control the order
    fieldnames = [
        "qid",
        "year",
        "subject",
        "no_subject",
        "no",
        "content_verbatim",
        "content_fixed",
        "choice_a",
        "choice_b",
        "choice_c",
        "choice_d",
        "answer",
        "chapter",
        "attachment_link",
        "mixed_choices",
    ]
    keys = list(dicts[0].keys())
    keys.remove("created_at")
    assert sorted(fieldnames) == sorted(
        keys
    ), f"Fieldnames do not match dict keys:\nFieldnames: {fieldnames}\nDict keys: {keys}"
    with open(THE_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        for d in dicts:
            del d["created_at"]
            for k, v in d.items():
                if isinstance(v, str):
                    assert (
                        CSV_DELIMITER not in v
                    ), f"Value contains delimiter {CSV_DELIMITER}: {v} for {d}"
                # We want to write actual booleans as TRUE/FALSE, not 1/0 or yes/no
                if isinstance(v, bool):
                    d[k] = "TRUE" if v else "FALSE"
            writer.writerow(d)

    print("Exported consolidated_questions.csv")


def import_tsv(engine):
    if not THE_TSV.exists():
        log.error(f"TSV file not found at {THE_TSV}")
        return

    questions = []
    with open(THE_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
        for row in reader:
            if not row or not row.get("qid"):
                continue
            qid = row["qid"].strip()
            if not qid:
                continue

            year = int(row["year"])
            subject = int(row["subject"])
            no_subject = int(row["no_subject"])
            no = int(row["no"])
            content_verbatim = row["content_verbatim"]
            content_fixed = row["content_fixed"] if row.get("content_fixed") else None
            choice_a = row["choice_a"]
            choice_b = row["choice_b"]
            choice_c = row["choice_c"]
            choice_d = row["choice_d"]
            answer = int(row["answer"])
            chapter = row["chapter"] if row.get("chapter") else None
            attachment_link = (
                row["attachment_link"] if row.get("attachment_link") else None
            )

            mixed_choices = None
            if row.get("mixed_choices"):
                mc_str = row["mixed_choices"].strip().upper()
                if mc_str == "TRUE":
                    mixed_choices = True
                elif mc_str == "FALSE":
                    mixed_choices = False

            q = ConsolidatedQuestion(
                qid=qid,
                year=year,
                subject=subject,
                no_subject=no_subject,
                no=no,
                content_verbatim=content_verbatim,
                content_fixed=content_fixed,
                choice_a=choice_a,
                choice_b=choice_b,
                choice_c=choice_c,
                choice_d=choice_d,
                answer=answer,
                chapter=chapter,
                attachment_link=attachment_link,
                mixed_choices=mixed_choices,
            )
            questions.append(q)

    with Session(engine) as session:
        ConsolidatedQuestion.__table__.drop(engine, checkfirst=True)
        ConsolidatedQuestion.__table__.create(engine, checkfirst=True)
        for q in questions:
            session.add(q)
        session.commit()

    print(f"Imported {len(questions)} consolidated questions from TSV into database.")


def gen_and_export(engine):
    gen_consolidated(engine)
    export_csv(engine)


Decision = dict[str, object]


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
        for pair_key_, value in all_decisions():
            if value.get("applied"):
                continue
            applied += 1
            canonical = value.get("canonical")
            decision_type = value["type"]
            assert isinstance(canonical, str) or canonical is None
            assert isinstance(decision_type, str)
            if decision_type == "canonical" and canonical:
                names = pair_key_.split("|")
                assert len(names) == 2, f"Unexpected pair key: {pair_key_}"
                non_canonical = names[0] if names[1] == canonical else names[1]
                old_stem = Path(non_canonical).stem
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
            existing = session.get(ImageDedupDecision, pair_key_)
            if existing is None:
                session.add(
                    ImageDedupDecision(
                        pair_key=pair_key_,
                        decision=decision_type,
                        canonical=canonical,
                    )
                )
            else:
                existing.decision = decision_type
                existing.canonical = canonical
                session.add(existing)
            value["applied"] = True
            DECISIONS.set(dedup_cache_key(pair_key_), value)
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


def render_pair_page(pair: SimilarPair, attachment_map: dict[str, list[dict]]) -> str:
    key = pair_key(pair)
    a_qs = questions_for_image(attachment_map, pair.a.name)
    b_qs = questions_for_image(attachment_map, pair.b.name)

    def panel(image: Fingerprint, questions: list[dict]) -> str:
        return (
            f"<div class='panel'><h2>{html.escape(image.name)}</h2>"
            f"<img src='/img/{image.name}' alt='{html.escape(image.name)}'>"
            f"<p class='muted'>{image.size[0]} &times; {image.size[1]} px</p>"
            f"{render_questions(questions)}</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Review duplicate images</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;color:#1f2937;max-width:1200px}}
header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e5e7eb;padding-bottom:.5rem;margin-bottom:1rem}}
.meta{{color:#6b7280;font-size:.9rem}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
.panel{{border:1px solid #d1d5db;border-radius:8px;padding:1rem;background:#fafafa}}
.panel img{{max-width:100%;height:auto;border:1px solid #e5e7eb;background:#fff}}
.panel ul{{font-size:.85rem;padding-left:1.2rem}}
.actions{{display:flex;gap:.5rem;margin-top:1rem}}
button{{padding:.6rem .9rem;border-radius:6px;border:1px solid #d1d5db;cursor:pointer;font-size:.9rem}}
.reject{{background:#fee2e2}}
.canonical{{background:#dcfce7}}
.muted{{color:#9ca3af}}
</style>
</head>
<body>
<header>
  <div><strong>Duplicate image review</strong> &mdash; ssim={pair.ssim:.3f}, dist={pair.dist}</div>
  <form method="post" action="/reset"><button type="submit" class="muted">Reset all decisions</button></form>
</header>
<div class="pair">
  {panel(pair.a, a_qs)}
  {panel(pair.b, b_qs)}
</div>
<div class="actions">
  <form method="post" action="/decision">
    <input type="hidden" name="key" value="{html.escape(key)}">
    <button type="submit" name="decision" value="canonical:{pair.a.name}" class="canonical">A is canonical</button>
    <button type="submit" name="decision" value="canonical:{pair.b.name}" class="canonical">B is canonical</button>
    <button type="submit" name="decision" value="reject" class="reject">Reject (not a duplicate)</button>
  </form>
</div>
</body>
</html>"""


def render_done_page(pairs: Sequence[SimilarPair]) -> str:
    rows = []
    unapplied = 0
    for pair in pairs:
        decision = get_decision(pair_key(pair))
        if decision is None:
            continue
        applied = decision.get("applied", False)
        if not applied:
            unapplied += 1
        label = (
            f"canonical: {decision['canonical']}"
            if decision.get("type") == "canonical"
            else "rejected"
        )
        if applied:
            label += " (applied)"
        rows.append(
            f"<li><code>{html.escape(pair_key(pair))}</code> &rarr; "
            f"{html.escape(label)}</li>"
        )
    if unapplied:
        apply_html = (
            "<form method='post' action='/apply'>"
            f"<button type='submit'>Save {unapplied} decisions to database + TSV</button>"
            "</form>"
        )
    else:
        apply_html = "<p class='muted'>All decisions applied to database and TSV.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Duplicate review complete</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;color:#1f2937}}
code{{background:#f3f4f6;padding:.1rem .3rem;border-radius:4px}}
.muted{{color:#9ca3af}}
button{{padding:.6rem .9rem;border-radius:6px;border:1px solid #d1d5db;cursor:pointer;font-size:.9rem}}
</style>
</head>
<body>
<h1>All pairs reviewed</h1>
<p class="muted">{len(rows)} decisions recorded.</p>
<ul>{''.join(rows)}</ul>
{apply_html}
<form method="post" action="/reset"><button type="submit">Reset all decisions</button></form>
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
    pairs: list[SimilarPair]
    attachment_map: dict[str, list[dict]]
    name_to_path: dict[str, Path]
    converted: dict[str, bytes]

    def __init__(
        self,
        engine,
        pairs: list[SimilarPair],
        attachment_map: dict[str, list[dict]],
        name_to_path: dict[str, Path],
    ) -> None:
        self.engine = engine
        self.pairs = pairs
        self.attachment_map = attachment_map
        self.name_to_path = name_to_path
        self.converted = {}


def create_dedup_app(state: ReviewState) -> FastAPI:
    app = FastAPI(title="Duplicate image review")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        pending = [pair for pair in state.pairs if get_decision(pair_key(pair)) is None]
        if pending:
            return render_pair_page(pending[0], state.attachment_map)
        return render_done_page(state.pairs)

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
    def decision(key: str = Form(""), decision: str = Form("")) -> RedirectResponse:
        if decision.startswith("canonical:"):
            set_decision(
                key, {"type": "canonical", "canonical": decision.split(":", 1)[1]}
            )
        elif decision == "reject":
            set_decision(key, {"type": "reject"})
        return RedirectResponse("/", status_code=303)

    @app.post("/reset")
    def reset() -> RedirectResponse:
        clear_decisions()
        return RedirectResponse("/", status_code=303)

    @app.post("/apply")
    def apply() -> RedirectResponse:
        apply_decisions(state.engine)
        return RedirectResponse("/", status_code=303)

    return app


def review_image_duplicates(engine, args) -> None:
    if not args.skip_import:
        print("Importing current TSV into database...")
        import_tsv(engine)
    print("Scanning images for duplicates...")
    exact, pairs = find_duplicate_groups(
        ANNALES_IMG_DIR,
        args.threshold,
        args.ssim_threshold,
        verbose=True,
    )
    if exact:
        print("=== Exact duplicates (identical bytes) ===")
        for names in exact.values():
            print("  " + " == ".join(names))
    pending = [pair for pair in pairs if get_decision(pair_key(pair)) is None]
    print(f"{len(pairs)} similar pairs found, {len(pending)} pending review")
    if not pairs:
        return
    attachment_map = build_attachment_map(engine)
    name_to_path = {p.a.name: p.a.path for p in pairs}
    name_to_path.update({p.b.name: p.b.path for p in pairs})
    state = ReviewState(
        engine=engine,
        pairs=pairs,
        attachment_map=attachment_map,
        name_to_path=name_to_path,
    )
    app = create_dedup_app(state)
    print(f"Dedup review app running at http://localhost:{args.port}")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    engine = create_engine()
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "gen-consolidated": gen_consolidated,
        "gen-consolidated-pdf": gen_consolidated_pdf,
        "import-tsv": import_tsv,
        "export-csv": export_csv,
        "gen+export": gen_and_export,
        "add_subject_to_csv": add_subject_to_csv,
        "change_chapters_to_number_csv": change_chapters_to_number_csv,
    }
    run_subparser = subparsers.add_parser("run", help="Run a command")
    run_subparser.add_argument(
        "command",
        choices=commands.keys(),
        help="Command to run",
    )
    run_subparser.set_defaults(func=lambda args: commands[args.command](engine))
    dedup_parser = subparsers.add_parser(
        "dedup-images",
        help="Import TSV, detect duplicate images and review them via a local web app",
    )
    dedup_parser.add_argument(
        "--port", type=int, default=DEDUP_PORT, help=f"Port (default: {DEDUP_PORT})"
    )
    dedup_parser.add_argument(
        "--threshold",
        type=int,
        default=DEDUP_THRESHOLD,
        help=f"Max Hamming distance (default: {DEDUP_THRESHOLD})",
    )
    dedup_parser.add_argument(
        "--ssim-threshold",
        type=float,
        default=DEDUP_SSIM_THRESHOLD,
        help=f"Min SSIM score (default: {DEDUP_SSIM_THRESHOLD})",
    )
    dedup_parser.add_argument(
        "--skip-import",
        action="store_true",
        default=False,
        help="Do not re-import the TSV before scanning",
    )
    dedup_parser.set_defaults(func=lambda args: review_image_duplicates(engine, args))
    args = parser.parse_args()
    args.func(args)


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
