#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import re
import time

import requests

from typing import Literal
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from sqlmodel import Session

from cache import CACHE
from models import AnnaleQuestion, create_engine

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
# order of subjects in which they appear
SUBJECTS: list[Subject] = ["mto", "amv", "cda", "nrs", "his", "ang"]


def subject_symbol(sub: Subject) -> str:
    if sub == "mto":
        return "1"
    elif sub == "amv":
        return "2"
    elif sub == "cda":
        return "3"
    elif sub == "nrs":
        return "4"
    elif sub == "his":
        return "5"
    elif sub == "ang":
        return "F"


# text between <style> and </style>
def get_style(soup) -> str:
    return soup.find("style").string


ZeroToThree = Literal[0, 1, 2, 3]


def get_answers(style_txt: str) -> list[ZeroToThree]:
    # all answer are elements of type repa1 repb2, etc, so we can search for rep followed by a number and a letter
    # get all from regex in text
    matches = re.findall(r"rep([a-d])\d+", style_txt)
    assert len(matches) >= 20, f"Not enough answers, got {len(matches)}"
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
    y: Year,
    sub: Subject,
    soup: BeautifulSoup,
    answers: list[ZeroToThree],
    no_past_questions: int,
) -> list[AnnaleQuestion]:
    questions: list[AnnaleQuestion] = []
    i = 1
    while (outer_q_div := soup.find("div", id=f"q{i}")) is not None:
        q_div = outer_q_div.find("div", class_="q")
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
        q_txt = re.sub(r"^\d+ -\s*", "", q_div.text).replace("⚠️", "").strip()
        options = r_div.find_all("p")
        q_answers = []
        for option in options:
            label = option.find("label").text  # type: ignore
            # remove "A- ", "B- ", etc
            answer_text = re.sub(r"^[A-D]-\s*", "", label).strip()
            q_answers.append(answer_text)

        q_number = f"{subject_symbol(sub)}.{i}"
        questions.append(
            AnnaleQuestion(
                year=y,
                question_number=q_number,
                question_id=f"{y}-{q_number}",
                content=q_txt,
                choice_a=q_answers[0],
                choice_b=q_answers[1],
                choice_c=q_answers[2],
                choice_d=q_answers[3],
                answer=answers[i - 1],
                attachment_link=attachment_link,
            )
        )
        i += 1
    return questions


class Req:
    def __init__(self) -> None:
        http = requests.Session()
        http.headers.update(HEADER)
        http.mount("https://", ADAPTER)
        http.mount("http://", ADAPTER)
        self.http = http

    @CACHE.memoize(ignore=(0,))
    def get_correction_page_str(self, y: Year, sub: Subject) -> str:
        url = f"{ANNALES_DOMAIN}/back/correction.php?annee={y}&theme={sub}"
        response = self.http.get(url)
        time.sleep(0.3)  # to avoid spamming, but skipping delay if cached
        return response.text.replace("&nbsp;", " ")

    def get_correction_page(self, y: Year, sub: Subject) -> BeautifulSoup:
        page_str = self.get_correction_page_str(y, sub)
        return BeautifulSoup(page_str, "html.parser")


def main():
    req = Req()
    all_questions: list[AnnaleQuestion] = []
    for y in YEARS:
        no_past_questions = 1
        for sub in SUBJECTS:
            # print(f"\rProcessing year {y}, subject {sub}...")
            soup = req.get_correction_page(y, sub)
            style_txt = get_style(soup)
            answers = get_answers(style_txt)
            questions = parse_questions(
                y, sub, soup, answers, no_past_questions=no_past_questions
            )
            all_questions.extend(questions)
            no_past_questions += len(questions)
    print(f"Total questions parsed: {len(all_questions)}")
    engine = create_engine()
    with Session(engine) as session:
        # print(f"Existing questions in database: {len(existing_qids)}")
        # print("all_questions", all_questions)
        for q in all_questions:
            session.add(q)
        session.commit()


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
