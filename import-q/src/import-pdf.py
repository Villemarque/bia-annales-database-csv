#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import csv
import logging
import logging.handlers
import os
import re
import argparse

from pathlib import Path
from typing import List, Literal

from rapidjson import Decoder, PM_COMMENTS, PM_TRAILING_COMMAS  # more lenient
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

logging.getLogger("pypdf").setLevel(logging.ERROR)
from google import genai
from google.genai import types

from cache import CACHE
from models import PdfQuestion, create_engine
from log import log, SCRIPT_DIR


load_dotenv()

#############
# Constants #
#############

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
assert GEMINI_API_KEY is not None, "GEMINI_API_KEY environment variable must be set"

GEMINI_MODEL = "gemini-3.6-flash"

########
# Logs #
########

###########
# Classes #
###########

Year = Literal[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
YEARS: list[Year] = [
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
]

ANNALES_PDF_DIR = SCRIPT_DIR.parent.parent / "annales-pdf"
print("ANNALES_PDF_DIR", ANNALES_PDF_DIR)

CHAPTER_NAMES = {
    0: "Les aéronefs",
    1: "Instrumentation",
    2: "Moteurs",
    3: "sustentation de l'aile",
    4: "Le vol stabilisé",
    5: "L'aérostation et le vol spatial",
    6: "L'atmosphère",
    7: "Les masses d'air et les fronts",
    8: "Les nuages",
    9: "Les vents",
    10: "Les phénomènes dangereux",
    11: "L'information météo",
    12: "Réglementation",
    13: "SV & FH",
    14: "Navigation",
}

prefix_explication = """# Si numéro de chapitre non présent, préfixer par :
    # 1 pour les question de Météo ex: "1.1", "1.2", ...
    # 2 pour les question d'aérodynamique ex: "2.1", "2.2", ...
    # 3 pour les question d'étude des aéronefs et engins spatiaux ex: "3.1", "3.2", ...
    # 4 pour les question de navigation ex: "4.1", "4.2", ...
    # 5 pour les question d'histoire ex: "5.1", "5.2", ...
    # F pour les questions de l'épreuve facultative d'anglais ex: "F.1", "F.2", ..."""

_chapter_options = "\n".join(
    f"    {cid} = {name}" for cid, name in sorted(CHAPTER_NAMES.items())
)

Q_PROMPT = f"""Extrait sous format JSON chaque question contenu dans ce document PDF.

Chapitres (id = nom) :
{_chapter_options}

Exemple de format de sortie JSON :
[
  {{
    year: 2017,
    question_number: "1.1",
    {prefix_explication}
    chapter: 6, # id du chapitre de la question, voir liste ci-dessus
    content: "Les deux principaux composants de l’air sec sont :",
    attachment: false, # if there is an image or diagram associated with the question
    choice_a: "l’azote et l’oxygène.",
    choice_b: "l’oxygène et le gaz carbonique.",
    choice_c: "l’azote et l'hélium.",
    choice_d: "l’oxygène et l’hydrogène.",
  }},
  ...
]"""

A_PROMPT_CSV = f"""Extrait sous format CSV chaque réponse contenue dans ce document PDF.

Chapitres (id = nom) :
{_chapter_options}

Exemple de format de sortie CSV:
question_id,answer,issue,chapter
2015-1.1,a,,6
2015-1.2,b,true,6
...

Avec "question_id" le format "année-numéro_de_question" (ex: "2015-1.1").
{prefix_explication}

Commence ta réponse par les en-têtes de colonnes, et ne fournis que le CSV, sans texte additionnel."""

A_PROMPT_JSON = f"""Extrait sous format JSON chaque réponse contenue dans ce document PDF.
Si la correction se présente sous la forme d'un tableau, la bonne réponse est la case grisée/hachurée.

Exemple de format de sortie JSON :
[
  {{
    question_id: "2015-1.1",
    answer: "a", # a, b, c ou d
    issue: false, # true si la question ou la réponse présente un problème
  }},
  ...
]
Avec "question_id" le format "année-numéro_de_question" (ex: "2015-1.1").
{prefix_explication}

Commence ta réponse par le JSON et ne fournis que le JSON, sans texte additionnel."""

A_PROMPT_AI = """Voici un sujet d'examen (sans correction). Détermine la bonne réponse de
chaque question, uniquement à partir de tes connaissances.

Exemple de format de sortie JSON :
[
  {{
    question_id: "2015-1.1",
    answer: "a", # a, b, c ou d
    issue: false, # true si la question ou la réponse présente un problème
  }},
  ...
]
Avec "question_id" le format "année-numéro_de_question" (ex: "2015-1.1").
{prefix_explication}

Commence ta réponse par le JSON et ne fournis que le JSON, sans texte additionnel."""


# here the questions in JSON are cached
# ignore by default the prompt, to delete it, increase version number
@CACHE.memoize(name="parse_pdf_raw_v5", ignore=(1,))
def parse_pdf_raw(filepath: Path, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf",
            ),
            prompt,
        ],
    )
    print(response)
    txt = response.text
    assert txt is not None, "No text returned from Gemini API"
    return txt


# here the answers in CSV are cached
@CACHE.memoize(name="parse_pdf_pro_raw_v1", ignore=(1,))
def parse_pdf_pro_raw(filepath: Path, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf",
            ),
            prompt,
        ],
    )
    print(response)
    txt = response.text
    assert txt is not None, "No text returned from Gemini API"
    return txt


# here the answers in JSON are cached
@CACHE.memoize(name="parse_pdf_pro_raw_json_v2", ignore=(1,))
def parse_pdf_pro_raw_json(filepath: Path, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf",
            ),
            prompt,
        ],
    )
    print(response)
    txt = response.text
    assert txt is not None, "No text returned from Gemini API"
    return txt


def render_exam(questions: list[PdfQuestion]) -> str:
    lines = []
    for q in questions:
        lines.append(f"{q.question_id}. {q.content}")
        lines.append(f"  A) {q.choice_a}")
        lines.append(f"  B) {q.choice_b}")
        lines.append(f"  C) {q.choice_c}")
        lines.append(f"  D) {q.choice_d}")
    return "\n".join(lines)


# here the AI answers are cached
@CACHE.memoize(name="parse_exam_answers_ai_v1", ignore=(1,))
def parse_exam_answers_ai(exam: str, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[exam, prompt],
    )
    print(response)
    txt = response.text
    assert txt is not None, "No text returned from Gemini API"
    return txt


def parse_json_llm(txt: str):
    raw_output = f"[{txt.partition('[')[2].rpartition(']')[0]}]"
    # print(raw_output[:])
    raw_output = raw_output.replace(
        "choice__d", "choice_d"
    )  # joy of non-determinism...
    decoder = Decoder(parse_mode=PM_COMMENTS | PM_TRAILING_COMMAS)
    return decoder(raw_output)


def parse_answers_json(y: Year) -> dict[str, tuple[str, bool, int | None]]:
    filepath = ANNALES_PDF_DIR / f"corrections/{y}-correction-bia+anglais.pdf"
    raw_output = parse_pdf_pro_raw_json(filepath, A_PROMPT_JSON)
    parsed_output = parse_json_llm(raw_output)
    res = {}
    # read json from parsed_output
    for row in parsed_output:
        question_id = row["question_id"]
        answer = row["answer"].strip().lower()
        issue = row["issue"]
        res[question_id] = (answer, issue, None)
    return res


def _chapter_from_csv(raw: str) -> int | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        cid = int(raw)
    except ValueError:
        return None
    return cid if cid in CHAPTER_NAMES else None


def parse_answers_csv(y: Year) -> dict[str, tuple[str, bool, int | None]]:
    filepath = ANNALES_PDF_DIR / f"corrections/{y}-correction-bia+anglais.pdf"
    raw_output = parse_pdf_pro_raw(filepath, A_PROMPT_CSV)
    # print(raw_output[:])
    # read csv from raw_output
    reader = csv.DictReader(raw_output.splitlines())
    res = {}
    for row in reader:
        question_id = row["question_id"]
        answer = row["answer"].strip().lower()
        issue = row["issue"].strip().lower() == "true"
        res[question_id] = (answer, issue, _chapter_from_csv(row.get("chapter", "")))
    return res


def parse_answers_ai(
    questions: list[PdfQuestion],
) -> dict[str, tuple[str, bool, int | None]]:
    raw_output = parse_exam_answers_ai(render_exam(questions), A_PROMPT_AI)
    parsed_output = parse_json_llm(raw_output)
    res = {}
    for row in parsed_output:
        question_id = row["question_id"]
        answer = row["answer"].strip().lower()
        issue = row["issue"]
        res[question_id] = (answer, issue, None)
    return res


def answer_to_int(answer: str) -> int:
    mapping = {"a": 0, "b": 1, "c": 2, "d": 3}
    return mapping[answer.lower()]


def parse_questions(y: Year) -> List[PdfQuestion]:
    filepath = ANNALES_PDF_DIR / f"sujets/{y}-examen-bia+anglais.pdf"
    parsed_output = parse_json_llm(parse_pdf_raw(filepath, Q_PROMPT))
    res = []
    # remove leading zeros if they exist
    for q in parsed_output:
        assert y == q["year"], f"Year mismatch: expected {y}, got {q['year']}"
        q["question_number"] = re.sub(r"\.0", ".", q["question_number"])
        question_id = f"{q['year']}-{q['question_number']}"
        print("\rquestion_id", question_id, end="")
        pq = PdfQuestion(
            question_id=question_id,
            year=q["year"],
            question_number=q["question_number"].strip(),
            content=q["content"].strip(),
            choice_a=q["choice_a"].strip(),
            choice_b=q["choice_b"].strip(),
            choice_c=q["choice_c"].strip(),
            choice_d=q["choice_d"].strip(),
            attachment=q["attachment"],
            answer=None,  # to be filled later
        )
        pq.chapter = q.get("chapter") if q.get("chapter") in CHAPTER_NAMES else None
        if pq.chapter is None:
            pq.chapter = prompt_user_chapter(pq, None)
        res.append(pq)
    return res


def _stable_cache_arg(arg):
    if isinstance(arg, PdfQuestion):
        return ("PdfQuestion", arg.question_id)
    return arg


def memoize_stable(name):
    def decorator(func):
        cached = CACHE.memoize(name=name)(func)
        orig_key = cached.__cache_key__

        def __cache_key__(*args, **kwargs):
            args = tuple(_stable_cache_arg(a) for a in args)
            kwargs = {k: _stable_cache_arg(v) for k, v in kwargs.items()}
            return orig_key(*args, **kwargs)

        cached.__cache_key__ = __cache_key__
        return cached

    return decorator


@memoize_stable("disambiguate_answer_v3")
def prompt_user_answer(
    q: PdfQuestion, past: tuple[str, bool], ai: tuple[str, bool]
) -> str:
    choices = (q.choice_a, q.choice_b, q.choice_c, q.choice_d)
    print(f"\n--- Answer conflict for {q.question_id} ---")
    print(f"Content: {q.content}")
    for i, choice in enumerate(choices):
        print(f"  {chr(ord('A') + i)}) {choice}")
    print(f"Past answer (correction): {past[0].upper()}")
    print(f"AI answer (exam pass):    {ai[0].upper()}")
    while True:
        choice = (
            input("Which is correct? [a/b/c/d, Enter = keep past] ").strip().lower()
        )
        if choice == "":
            return past[0]
        if choice in "abcd":
            return choice
        print("Invalid input, try again.")


@memoize_stable("ask_chapter_v1")
def prompt_user_chapter(q: PdfQuestion, suggested: int | None) -> int | None:
    print(f"\n--- Chapter for {q.question_id} ---")
    print(f"Content: {q.content}")
    for cid in sorted(CHAPTER_NAMES):
        print(f"  {cid:2d}) {CHAPTER_NAMES[cid]}")
    print("  n) No chapter (histoire/anglais)")
    while True:
        choice = input("Chapter id [0-14, n = none]: ".strip()).strip().lower()
        if choice == "":
            return suggested
        if choice in ("n", "-"):
            return None
        try:
            cid = int(choice)
        except ValueError:
            cid = -1
        if cid in CHAPTER_NAMES:
            return cid
        print("Invalid input, try again.")


def process_questions_answer(add_db: bool, answer_json: bool):
    engine = create_engine()
    for y in YEARS:
        log.info(f"Processing year {y} (Q)...")
        questions = parse_questions(y)
        log.info(f"Processing year {y} (A) (json: {answer_json})...")
        if answer_json:
            answers = parse_answers_json(y)
        else:
            answers = parse_answers_csv(y)
        print("parsed answer", answers)
        log.info(f"Processing year {y} (AI answer pass)...")
        ai_answers = parse_answers_ai(questions)
        if y != 2026:  # DEBUG, only care about 2026, others checked manually beforehand
            ai_answers = {}
        print("parsed ai answer", ai_answers)
        with Session(engine) as session:
            for q in questions:
                # if session.get(PdfQuestion, q.question_id) is not None:
                #   continue
                answer = answers.get(q.question_id, None)
                ai = ai_answers.get(q.question_id, None)
                # chapter from the CSV answer pass (if provided and not already set)
                if answer is not None and answer[2] is not None and q.chapter is None:
                    q.chapter = answer[2]
                if (
                    answer is not None
                    and ai is not None
                    and answer[0].lower() != ai[0].lower()
                ):
                    answer = (prompt_user_answer(q, answer[:2], ai[:2]), answer[1])
                elif answer is None and ai is not None:
                    answer = ai
                assert answer is not None, (
                    f"No answer found for question_id {q.question_id}"
                )
                if answer[1]:  # if there are some issues with the question
                    q.has_issue = True
                else:
                    try:
                        q.answer = answer_to_int(answer[0])
                    except Exception as _:
                        log.warning(
                            f"No/bad answer found for question_id {q.question_id}, answer: {answer[0]}"
                        )
                if add_db:
                    session.add(q)
                    try:
                        session.commit()
                    except IntegrityError:
                        session.rollback()
                        log.warning(f"Duplicate question {q.question_id}, skipping.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--add-db",
        action="store_true",
        default=False,
        help="Save the result to SQLite",
    )
    parser.add_argument(
        "--answer-json",
        action="store_true",
        default=False,
        help="Use JSON format for answers instead of CSV",
    )
    parser.set_defaults(
        func=lambda args: process_questions_answer(args.add_db, args.answer_json)
    )
    args = parser.parse_args()
    args.func(args)


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
