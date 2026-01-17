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

from io import BytesIO
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
from pypdf import PdfWriter
logging.getLogger("pypdf").setLevel(logging.ERROR)
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

ANNALES_PDF_DIR = SCRIPT_DIR.parent.parent / f"annales-pdf"
print("ANNALES_PDF_DIR", ANNALES_PDF_DIR)

PROMPT = """Extrait sous format JSON chaque question contenu dans ce document PDF.

Exemple de format de sortie JSON :
[
  {
    year: 2017,
    question_number: "1.1",
    # Si numéro de chapitre non présent, préfixer par :
    # 1 pour les question de Météo ex: "1.1", "1.2", ...
    # 2 pour les question d'aérodynamique ex: "2.1", "2.2", ...
    # 3 pour les question d'étude des aéronefs et engins spatiaux ex: "3.1", "3.2", ...
    # 4 pour les question de navigation ex: "4.1", "4.2", ...
    5 pour les question d'histoire ex: "5.1", "5.2", ...
    # F pour les questions de l'épreuve facultative d'anglais ex: "F.1", "F.2", ... 
    content: "Les deux principaux composants de l’air sec sont :",
    attachment: false, # if there is an image or diagram associated with the question
    choice_a: "l’azote et l’oxygène.",
    choice_b: "l’oxygène et le gaz carbonique.",
    choice_c: "l’azote et l'hélium.",
    choice_d: "l’oxygène et l’hydrogène.",
  },
  ...
]"""

# as bytes and not bytesIO to be cacheable
@CACHE.memoize(name="parse_pdf_raw_v3")
def parse_pdf_raw(year: Year) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    filepath = ANNALES_PDF_DIR / f"sujets/{year}-examen-bia+anglais.pdf"
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
    raw_output = raw_output.replace("choice__d", "choice_d") # joy of non-determinism...
    decoder = Decoder(parse_mode=PM_COMMENTS | PM_TRAILING_COMMAS)
    parsed_output = decoder(raw_output)
    res = []
    for q in parsed_output:
        assert y == q["year"], f"Year mismatch: expected {y}, got {q['year']}"
        question_id = f"{q["year"]}-{q['question_number']}"
        print("\rquestion_id", question_id,end="")
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
    for y in YEARS:
        log.info(f"Processing years {y}...")
        questions = parse_pdf(y)
        with Session(engine) as session:
            for q in questions:
                pass
                #session.add(q)
            #session.commit()
        log.info(f"Inserted questions from year {y} into database.")


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
