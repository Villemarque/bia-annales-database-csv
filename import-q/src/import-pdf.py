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

########
# Logs #
########

###########
# Classes #
###########

Year = Literal[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
YEARS: list[Year] = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

ANNALES_PDF_DIR = SCRIPT_DIR.parent.parent / "annales-pdf"
print("ANNALES_PDF_DIR", ANNALES_PDF_DIR)

prefix_explication = """# Si numéro de chapitre non présent, préfixer par :
    # 1 pour les question de Météo ex: "1.1", "1.2", ...
    # 2 pour les question d'aérodynamique ex: "2.1", "2.2", ...
    # 3 pour les question d'étude des aéronefs et engins spatiaux ex: "3.1", "3.2", ...
    # 4 pour les question de navigation ex: "4.1", "4.2", ...
    # 5 pour les question d'histoire ex: "5.1", "5.2", ...
    # F pour les questions de l'épreuve facultative d'anglais ex: "F.1", "F.2", ..."""

Q_PROMPT = f"""Extrait sous format JSON chaque question contenu dans ce document PDF.

Exemple de format de sortie JSON :
[
  {{
    year: 2017,
    question_number: "1.1",
    {prefix_explication}
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

Exemple de format de sortie CSV:
question_id,answer,issue
2015-1.1,a,,
1015-1.2,b,true,
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


# here the questions in JSON are cached
# ignore by default the prompt, to delete it, increase version number
@CACHE.memoize(name="parse_pdf_raw_v4", ignore=(1,))
def parse_pdf_raw(filepath: Path, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
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
        model="gemini-3-pro-preview",
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
@CACHE.memoize(name="parse_pdf_pro_raw_json_v1", ignore=(1,))
def parse_pdf_pro_raw_json(filepath: Path, prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
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


def parse_json_llm(txt: str):
    raw_output = f"[{txt.partition('[')[2].rpartition(']')[0]}]"
    print(raw_output[:])
    raw_output = raw_output.replace(
        "choice__d", "choice_d"
    )  # joy of non-determinism...
    decoder = Decoder(parse_mode=PM_COMMENTS | PM_TRAILING_COMMAS)
    return decoder(raw_output)


def parse_answers_json(y: Year) -> dict[str, tuple[str, bool]]:
    filepath = ANNALES_PDF_DIR / f"corrections/{y}-correction-bia+anglais.pdf"
    raw_output = parse_pdf_pro_raw_json(filepath, A_PROMPT_CSV)
    parsed_output = parse_json_llm(raw_output)
    # print(raw_output[:])
    res = {}
    # read json from parsed_output
    for row in parsed_output:
        question_id = row["question_id"]
        answer = row["answer"].strip().lower()
        issue = row["issue"]
        res[question_id] = (answer, issue)
    return res


def parse_answers_csv(y: Year) -> dict[str, tuple[str, bool]]:
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
        res[question_id] = (answer, issue)
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
        res.append(
            PdfQuestion(
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
        )
    return res


def process_questions_answer(add_db: bool, answer_json: bool):
    engine = create_engine()
    for y in YEARS:
        log.info(f"Processing year {y} (Q)...")
        questions = parse_questions(y)
        log.info(f"Processing year {y} (A)...")
        if answer_json:
            answers = parse_answers_json(y)
        else:
            answers = parse_answers_csv(y)
        print("parsed answer", answers)
        with Session(engine) as session:
            for q in questions:
                # if session.get(PdfQuestion, q.question_id) is not None:
                #   continue
                answer = answers.get(q.question_id, None)
                if answer is None:
                    log.warning(f"No answer found for question_id {q.question_id}")
                    continue
                elif answer[1]:  # if there are some issues with the question
                    q.has_issue = True
                else:
                    print("setting answer for", q.question_id, "to", answer[0])
                    try:
                        q.answer = answer_to_int(answer[0])
                    except Exception as _:
                        pass
                if add_db:
                    session.add(q)
            if add_db:
                session.commit()
            log.info(f"Inserted questions from year {y} into database.")


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
