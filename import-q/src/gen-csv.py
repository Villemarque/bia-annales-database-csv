#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations

import argparse

import Levenshtein

from difflib import ndiff
from argparse import RawTextHelpFormatter
from dataclasses import dataclass
from typing import Tuple, Protocol, Type, TypeVar, Generic, Sequence
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


def export_csv(engine):
    import csv

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
    with open(
        SCRIPT_DIR.parent.parent / "annales-bia.csv", "w", newline="", encoding="utf-8"
    ) as csvfile:
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
