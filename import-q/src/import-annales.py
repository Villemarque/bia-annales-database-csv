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

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

from models import AnnaleQuestion
from log import log

#############
# Constants #
#############

RETRY_STRAT = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRAT)

ANNALES_DOMAIN = "https://annales-bia.fr"

HEADER = {"User-Agent": "https://github.com/Villemarque/bia-annales-database-csv"}

########
# Logs #
########

###########
# Classes #
###########

Year = Literal[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
YEARS: list[Year] = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

Subject = Literal["mto", "amv", "cda", "nrs", "his", "ang"]
SUBJECTS: list[Subject] = ["cda", "amv", "mto", "nrs", "his", "ang"]


# question number in the exam of that year
def question_number(sub: Subject, no: int) -> int:
    if sub == "cda":
        return no
    elif sub == "amv":
        return no + 20
    elif sub == "mto":
        return no + 40
    elif sub == "nrs":
        return no + 60
    elif sub == "his":
        return no + 80
    # arbitrary place english at last
    elif sub == "ang":
        return no + 100


# text between <style> and </style>
def get_style(soup) -> str:
    return soup.find("style").string


ZeroToThree = Literal[0, 1, 2, 3]


def get_answers(style_txt: str) -> list[ZeroToThree]:
    # all answer are elements of type rep1a rep2b, etc, so we can search for rep followed by a number and a letter
    # get all from regex in text
    matches = re.findall(r"rep([a-d])\d+", style_txt)
    assert len(matches) == 20, f"Expected 20 matches, got {len(matches)}"
    indexes: dict[str, ZeroToThree] = {"a": 0, "b": 1, "c": 2, "d": 3}
    return [indexes[match] for match in matches]


# <form method="post" action="back/correction.php?annee=2015&amp;theme=mto">
#                                                 <div id="q1">
#                                 <div class="q"><p>1 - Le nuage figurant sur la photographie ci-contre est un&nbsp;: <img src="images/m1-2015.gif" alt="Nuage"> <em><a href="explications.php?id=2421" target="_blank">Explication</a></em></p></div>
#                                 <div class="r">
#                                     <p><input type="radio" name="q1" id="repa1" value="a"><label for="repa1">A- cirrus</label></p>
#                                     <p><input type="radio" name="q1" id="repb1" value="b"><label for="repb1">B- nimbostratus</label></p>
#                                     <p><input type="radio" name="q1" id="repc1" value="c"><label for="repc1">C- stratus</label></p>
#                                     <p><input type="radio" name="q1" id="repd1" value="d"><label for="repd1">D- cumulonimbus</label></p>
#                                 </div>
#                             </div>


def parse_questions(
    y: Year, sub: Subject, soup: BeautifulSoup, answers: list[ZeroToThree]
) -> list[AnnaleQuestion]:
    questions: list[AnnaleQuestion] = []
    for i in range(1, 21):
        q_div = soup.find("div", id=f"q{i}")
        assert q_div is not None, (
            f"Could not find question div for question {i} of {sub} {y}"
        )
        # get img if possible
        img_elm = q_div.find("img")
        if img_elm:
            img_src = img_elm["src"]
            # replace relative link with absolute link
            attachment_link = f"{ANNALES_DOMAIN}/{img_src}"
        else:
            attachment_link = None
        # remove <a href="explications.php?id=2421" target="_blank"> element from q_div
        a_elm = q_div.find("a", href=re.compile(r"explications\.php\?id=\d+"))
        if a_elm:
            a_elm.decompose()
        r_div = q_div.find_next_sibling("div", class_="r")
        assert r_div is not None, (
            f"Could not find answers div for question {i} of {sub} {y}"
        )
        # remove "1- ", "2- ", etc
        q_txt = re.sub(r"^[\d+] -\s*", "", q_div.text).strip()
        options = r_div.find_all("p")
        q_answers = []
        for option in options:
            label = option.find("label").text  # type: ignore
            # remove "A- ", "B- ", etc
            answer_text = re.sub(r"^[A-D]-\s*", "", label).strip()
            q_answers.append(answer_text)

        #         question_id: str = Field(primary_key=True)  # year-questionNumber
        # year: int = Field()
        # question_number: int = Field()
        # content: str = Field(max_length=1024)  # Optional description
        # choice_a: str = Field(min_length=1,nullable=False)
        # choice_b: str = Field(min_length=1,nullable=False)
        # choice_c: str = Field(min_length=1,nullable=False)
        # choice_d: str = Field(min_length=1,nullable=False)
        # answer: int = Field(min_length=1, max_length=1,nullable=False)  # 0, 1, 2, 3
        # attachment_link: Optional[str] = Field(default=None, max_length=256)
        questions.append(
            AnnaleQuestion(
                year=y,
                question_number=question_number(sub, i),
                question_id=f"{y}-{question_number(sub, i)}",
                content=q_txt,
                choice_a=q_answers[0],
                choice_b=q_answers[1],
                choice_c=q_answers[2],
                choice_d=q_answers[3],
                answer=answers[i - 1],
                attachment_link=attachment_link,
            )
        )
    return questions


class Req:
    def __init__(self) -> None:
        http = requests.Session()
        http.headers.update(HEADER)
        http.mount("https://", ADAPTER)
        http.mount("http://", ADAPTER)
        self.http = http

    def get_correction_page(self, y: Year, sub: Subject) -> BeautifulSoup:
        url = f"{ANNALES_DOMAIN}/back/correction.php?annee=2015&theme=mto"
        response = self.http.get(url)
        return BeautifulSoup(response.text)


def main():
    req = Req()
    all_questions: list[AnnaleQuestion] = []
    for y in YEARS:
        for sub in SUBJECTS:
            print(f"Processing year {y}, subject {sub}...")
            soup = req.get_correction_page(y, sub)
            style_txt = get_style(soup)
            answers = get_answers(style_txt)
            questions = parse_questions(y, sub, soup, answers)
            all_questions.extend(questions)
            time.sleep(0.3)
            break  # DEBUG
        break  # DEBUG
    print(f"Total questions parsed: {len(all_questions)}")
    for q in all_questions:
        print(q)
        print()


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
