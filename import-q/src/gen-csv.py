#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import argparse
import csv

import Levenshtein

from copy import deepcopy
from difflib import ndiff
from argparse import RawTextHelpFormatter
from dataclasses import dataclass
from typing import Tuple, Protocol, Type, TypeVar, Generic, Sequence, Iterable
from urllib3.util.retry import Retry

from requests.adapters import HTTPAdapter
import diskcache
from sqlmodel import Session, select, col
from sqlalchemy import and_

from models import (
    AfQuestion,
    AnnaleQuestion,
    create_engine,
    AnnaleToAfMapping,
    gen_unique_id,
    ConsolidatedQuestion,
)
from log import SCRIPT_DIR, log
from cache import CACHE

#############
# Constants #
#############

THE_CSV = SCRIPT_DIR.parent.parent / "annales-bia.csv"

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
                    col(AnnaleToAfMapping.is_same) == True,
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

            c = ConsolidatedQuestion(
                qid=gen_unique_id(),
                year=annale.year,
                label=annale.question_number,
                no=i,
                content_verbatim=annale.content,
                content_fixed=fixed,
                choice_a=annale.choice_a,
                choice_b=annale.choice_b,
                choice_c=annale.choice_c,
                choice_d=annale.choice_d,
                answer=annale.answer,
                chapter=af.chapter if af is not None else None,
                attachment_link=af.attachment_link
                if af is not None
                else annale.attachment_link,
                mixed_choices=af.mixed_choices if af is not None else None,
            )
            session.add(c)
            i += 1
        session.commit()


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


def write_csv(fieldnames, rows) -> None:
    with open(THE_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
            if row["chapter"] in ["5.", "6."]: # We do not split those into chapters
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
        "label",
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
    assert sorted(fieldnames) == sorted(keys), (
        f"Fieldnames do not match dict keys:\nFieldnames: {fieldnames}\nDict keys: {keys}"
    )
    with open(THE_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=CSV_DELIMITER)
        writer.writeheader()
        for d in dicts:
            del d["created_at"]
            for v in d.values():
                if isinstance(v, str):
                    assert CSV_DELIMITER not in v, (
                        f"Value contains delimiter {CSV_DELIMITER}: {v} for {d}"
                    )
            writer.writerow(d)

    print("Exported consolidated_questions.csv")


def gen_and_export(engine):
    gen_consolidated(engine)
    export_csv(engine)


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    engine = create_engine()
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "gen-consolidated": gen_consolidated,
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
    args = parser.parse_args()
    args.func(args)


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
