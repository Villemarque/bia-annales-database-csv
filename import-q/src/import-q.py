#!/usr/bin/env -S uv run --script

""""""

from __future__ import annotations

import argparse
import json
import logging
import datetime as dt
import logging.handlers
import os
import sys
import time

import selenium
import sqlmodel

from argparse import RawTextHelpFormatter
from collections import deque
from dataclasses import dataclass
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List, Union, Tuple

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlmodel import Field, SQLModel, Session, select

from models import QuestionId, Question

#############
# Constants #
#############

load_dotenv()

BIA_AF_EMAIL = os.getenv("BIA_AF_EMAIL", "")
BIA_AF_PASSWORD = os.getenv("BIA_AF_PASSWORD", "")
assert (
    BIA_AF_EMAIL and BIA_AF_PASSWORD
), "BIA_AF_EMAIL and BIA_AF_PASSWORD environment variables must be set"

DOMAIN = "https://bia-af.web.app"

SCRIPT_DIR = Path(__file__).resolve(strict=True).parent
LOG_PATH = f"{__file__}.log"

########
# Logs #
########

log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
format_string = "%(asctime)s | %(levelname)-8s | %(message)s"

# 125000000 bytes = 12.5Mb
handler = logging.handlers.RotatingFileHandler(
    LOG_PATH, maxBytes=12500000, backupCount=3, encoding="utf8"
)
handler.setFormatter(logging.Formatter(format_string))
handler.setLevel(logging.DEBUG)
log.addHandler(handler)

handler_2 = logging.StreamHandler(sys.stdout)
handler_2.setFormatter(logging.Formatter(format_string))
handler_2.setLevel(logging.INFO)
if __debug__:
    handler_2.setLevel(logging.DEBUG)
log.addHandler(handler_2)

###########
# Classes #
###########


def login(driver: webdriver.Chrome, email: str, password: str) -> None:
    # Access the domain's login page
    driver.get(DOMAIN)

    # Wait for the email input field to be visible and interactable
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "input-email"))
    )
    email_input.send_keys(email)

    # Wait for the password input field to be visible and interactable
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "input-password"))
    )
    password_input.send_keys(password)

    # Wait for the login button to be visible and interactable
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Connexion')]")
        )
    )
    # time.sleep(5)
    login_button.click()


def get_to_question_list_page(driver: webdriver.Chrome) -> None:
    driver.get(f"{DOMAIN}/questions")

    # Workaround a website's bug. Must go to Accueil first before returning to Questions.
    # Wait for the "Accueil" button to be visible and clickable
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Accueil')]"))
    )
    time.sleep(0.2)
    accueil_span = driver.find_element(By.XPATH, "//span[contains(text(), 'Accueil')]")
    accueil_span.click()
    time.sleep(0.2)

    # Wait for the "Questions" button to be visible and clickable
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Questions')]"))
    )
    questions_span = driver.find_element(
        By.XPATH, "//span[contains(text(), 'Questions')]"
    )
    questions_span.click()


def get_all_ids(driver: webdriver.Chrome) -> List[str]:
    # Initialize an empty list to store extracted IDs
    extracted_ids = []

    # Find all relevant <div> elements using the corresponding CSS selector
    first_column_divs = driver.find_elements(
        By.CSS_SELECTOR,
        "tbody[ng2-st-tbody] tr.ng2-smart-row.ng-star-inserted td.ng-star-inserted:nth-child(1) div.ng-star-inserted",
    )
    extracted_ids = [div.text for div in first_column_divs]
    return extracted_ids


def insert_questions_bulk(ids: list[str], engine):
    questions = [
        QuestionId(
            question_id=id_,
        )
        for id_ in ids
    ]

    with Session(engine) as session:
        for question in questions:
            existing = session.get(QuestionId, question.question_id)
            if not existing:
                session.add(question)
        session.commit()


def click_next(driver: webdriver.Chrome) -> None:
    # Wait until the "Next" button is clickable
    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a.ng2-smart-page-link.page-link-next")
        )
    )
    # Click the "Next" button
    next_button.click()


def find_by_css(driver: webdriver.Chrome, css_selector: str, timeout: int = 10) -> selenium.webdriver.remote.webelement.WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )

def find_by_css_multiples(driver: webdriver.Chrome, css_selector: str, timeout: int = 10) -> selenium.webdriver.remote.webelement.WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
    )

def parse_question(driver: webdriver.Chrome, q: QuestionId) -> Question:
    driver.get(f"{DOMAIN}/questions/{q.question_id}")

    question_id_elm = find_by_css(driver, "input[name='id']")
    question_id = question_id_elm.get_attribute("value")
    assert (
        question_id == q.question_id
    ), f"Question ID mismatch: expected {q.question_id}, got {question_id}"

    date_input = find_by_css(driver,"input[name='timestamp']")

    date_string = date_input.get_attribute("value")
    date_added = datetime.strptime(date_string, "%d/%m/%Y").date()

    # Extract Content (Question Text)
    content = find_by_css(driver, "input[name='text']").get_attribute(
        "value"
    )

    # Extract Choices (A, B, C, D)
    choices = find_by_css_multiples(driver,".form-group.answers .form-group.answer input[type='text']")
    choice_a = choices[0].get_attribute("value")
    choice_b = choices[1].get_attribute("value")
    choice_c = choices[2].get_attribute("value")
    choice_d = choices[3].get_attribute("value")

    # Extract Answer (Which choice is selected)
    answer_radio_buttons = find_by_css_multiples(driver, ".form-group.answers .form-group.answer input[type='radio']")
    answer_index = next(
        (i for i, btn in enumerate(answer_radio_buttons) if btn.is_selected()), None
    )
    assert answer_index is not None, "No answer selected"

    # Extract Chapter
    chapter = find_by_css(driver, "nb-select button.select-button").text.split(" ")[0]
    try:
        img_element = find_by_css(driver,"div.file_display.ng-star-inserted img",timeout=.4)
        print("Found attachment image", img_element)
        attachment_link = img_element.get_attribute("src")
        print("Attachment link:", attachment_link)
    except (selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.TimeoutException):
        attachment_link = None

    mixed_choices_checkbox = find_by_css(driver,".form-group.checkbox input[type='checkbox']")

    mixed_choices = mixed_choices_checkbox.is_selected()
    return Question(
        question_id=q.question_id,
        content=content,
        choice_a=choice_a,
        choice_b=choice_b,
        choice_c=choice_c,
        choice_d=choice_d,
        answer=answer_index,
        date_added=date_added,
        chapter=chapter,
        attachment_link=attachment_link,
        mixed_choices=mixed_choices,
    )


def populate_questions(
    driver: webdriver.Chrome, engine, qids_opt: list[str] | None = None
) -> None:
    with sqlmodel.Session(engine) as session:
        # find all qids from qids_opt
        if qids_opt is not None:
            stmt = select(QuestionId).where(QuestionId.question_id.in_(qids_opt))
        else:
            stmt = select(QuestionId).where(QuestionId.checked_at == None)
        qids = session.exec(stmt).all()
        for qid in qids:
            populated = parse_question(driver, qid)
            print(f"Populated question {populated}")
            session.add(populated)
            qid.checked_at = datetime.now(timezone.utc)
            session.add(qid)
            session.commit()
            time.sleep(0.3)


def driver_get_question_ids(driver: webdriver.Chrome, engine, *args) -> None:
    get_to_question_list_page(driver)
    while "there is a next button":
        time.sleep(0.5)
        ids = get_all_ids(driver)
        insert_questions_bulk(ids, engine)
        try:
            click_next(driver)
        except Exception as e:
            log.info("No more next button, exiting loop.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    commands = {
        "get_ids": driver_get_question_ids,
        "populate_questions": populate_questions,
    }
    parser.add_argument("command", choices=commands.keys())
    parser.add_argument(
        "-q",
        "--qids",
        nargs="*",
        help="List of question IDs to populate (only for populate_questions command)",
        default=None,
    )
    args = parser.parse_args()
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)
    login(driver, BIA_AF_EMAIL, BIA_AF_PASSWORD)
    time.sleep(1)
    engine = sqlmodel.create_engine("sqlite:///questions.db")
    SQLModel.metadata.create_all(engine)
    commands[args.command](driver, engine, args.qids)


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
