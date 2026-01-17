#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
import re
import time

import requests

from argparse import RawTextHelpFormatter
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List, Union, Tuple, Literal
from urllib3.util.retry import Retry

from rapidjson import Decoder, PM_COMMENTS, PM_TRAILING_COMMAS  # more lenient
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
import diskcache
from sqlmodel import Session, select
from google import genai
from google.genai import types
from dotenv import load_dotenv

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


PROMPT = """Extrait sous format JSON chaque question contenu dans ce document PDF.

Exemple de format de sortie JSON :
[
  {
    year: 2017,
    question_number: "1.1",
    content: "Les deux principaux composants de l’air sec sont :",
    attachment: false, # if there is an image or diagram associated with the question
    choice_a: "l’azote et l’oxygène.",
    choice_b: "l’oxygène et le gaz carbonique.",
    choice_c: "l’azote et l'hélium.",
    choice_d: "l’oxygène et l’hydrogène.",
  },
  ...
]"""


@CACHE.memoize()
def parse_pdf_raw(y: Year) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Retrieve and encode the PDF byte
    filepath = Path(
        SCRIPT_DIR.parent.parent / f"annales-pdf/sujets/{y}-examen-bia+anglais.pdf"
    )
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type="application/pdf",
            ),
            PROMPT,
        ],
    )
    txt = response.text
    assert txt is not None, "No text returned from Gemini API"
    return txt


def parse_pdf(y: Year) -> List[PdfQuestion]:
    raw_output = f"[{parse_pdf_raw(y).partition('[')[2].rpartition(']')[0]}]"
    print(raw_output[:])
    decoder = Decoder(parse_mode=PM_COMMENTS | PM_TRAILING_COMMAS)
    parsed_output = decoder(raw_output)
    res = []
    for q in parsed_output:
        assert y == q["year"], f"Year mismatch: expected {y}, got {q['year']}"
        question_id = f"{y}-{q['question_number']}"
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
            )
        )
    return res


def main():
    engine = create_engine()
    with Session(engine) as session:
        years: list[Year] = [2022]
        for year in years:
            log.info(f"Processing year {year}...")
            questions = parse_pdf(year)
            for q in questions:
                session.add(q)
            session.commit()
            log.info(f"Inserted questions for year {year} into the database.")


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
