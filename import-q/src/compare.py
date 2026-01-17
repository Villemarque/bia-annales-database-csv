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
import Levenshtein

from difflib import ndiff
from argparse import RawTextHelpFormatter
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    List,
    Union,
    Tuple,
    Literal,
    Protocol,
    Type,
    TypeVar,
    Generic,
)
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
import diskcache
from sqlmodel import Session, select

from models import AfQuestion, AnnaleQuestion, create_engine, PdfQuestion
from log import log, SCRIPT_DIR
from cache import CACHE

#############
# Constants #
#############

CACHE = diskcache.Cache(SCRIPT_DIR.parent / "cache")

RETRY_STRAT = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRAT)

########
# Logs #
########

###########
# Classes #
###########


def colored_diff_lines(s1, s2):
    RESET = "\033[0m"
    RED = "\033[91m"  # for deletions (s1)
    GREEN = "\033[92m"  # for additions (s2)

    # diff by character
    diff = list(ndiff(list(s1), list(s2)))
    line1 = []
    line2 = []

    for token in diff:
        code, char = token[:2], token[2:]
        if code == "  ":
            line1.append(char)
            line2.append(char)
        elif code == "- ":
            line1.append(f"{RED}{char}{RESET}")
            line2.append(" ")
        elif code == "+ ":
            line1.append(" ")
            line2.append(f"{GREEN}{char}{RESET}")

    return "".join(line1), "".join(line2)


class CleanContent(Protocol):
    def clean_content(self) -> str: ...


A = TypeVar("A", bound=CleanContent)
B = TypeVar("B", bound=CleanContent)


@dataclass(frozen=True)
class Diff(Generic[A, B]):
    ids: Tuple[A, B]
    leven_dist: int

    @classmethod
    def new(cls: Type["Diff[A, B]"], a: A, b: B) -> "Diff[A, B]":
        return cls(
            ids=(a, b),
            leven_dist=Levenshtein.distance(a.clean_content(), b.clean_content()),
        )


def compute_diffs_annale_af(engine) -> dict[int, list[Diff]]:
    with Session(engine) as session:
        a_s = session.exec(select(AfQuestion)).all()
        b_s = session.exec(select(AnnaleQuestion)).all()
        return compute_diffs(a_s, b_s)

def compute_diffs_annale_pdf_22(engine) -> dict[int, list[Diff]]:
    with Session(engine) as session:
        a_s = session.exec(select(AnnaleQuestion).where(AnnaleQuestion.year == 2022)).all()
        b_s = session.exec(select(PdfQuestion)).all()
        return compute_diffs(a_s, b_s)


@CACHE.memoize(name="compute_diffs_v2")
def compute_diffs(
    a_s: list[A],
    b_s: list[B],
) -> dict[int, list[Diff]]:
    res: dict[int, list[Diff]] = {}
    assert len(a_s) <= len(b_s)
    for (
        a
    ) in a_s:  # it's important to have af in outer loop as they're fewer of them
        min_diff: Diff | None = None
        for b in b_s:
            diff = Diff.new(a, b)
            min_diff = min(diff, min_diff or diff, key=lambda d: d.leven_dist)
        assert min_diff is not None
        previous = res.get(min_diff.leven_dist, [])
        previous.append(min_diff)
        res[min_diff.leven_dist] = previous  # in case it was not previously set
    return res


def check_identicals(engine) -> None:
    res = compute_diffs_annale_af(engine)
    for k in sorted(res.keys()):
        print(f"levenshtein distance: {k}, number of questions {len(res[k])}")


def sub_show_diffs(engine, min_leven_dist: int) -> None:
    res = compute_diffs_annale_af(engine)
    print(f"\nShowing diffs with minimum Levenshtein distance of {min_leven_dist}:\n")
    for k in sorted(res.keys()):
        if k >= min_leven_dist:
            print(
                f"\n\n=== Levenshtein distance: {k}, number of questions {len(res[k])} ==="
            )
            for diff in res[k]:
                af, annale = diff.ids
                print(
                    f"\n--- AfQuestion ID: {af.question_id} | AnnaleQuestion ID: {annale.question_id} ---"
                )
                af_diff, annale_diff = colored_diff_lines(af.content, annale.content)
                print("af:     |", af_diff)
                print("annale  |", annale_diff)


def show_diffs_22(engine) -> None:
    res = compute_diffs(engine, AnnaleQuestion, AfQuestion)
    print(f"\nShowing diffs with minimum Levenshtein distance of {min_leven_dist}:\n")
    for k in sorted(res.keys()):
        if k >= min_leven_dist:
            print(
                f"\n\n=== Levenshtein distance: {k}, number of questions {len(res[k])} ==="
            )
            for diff in res[k]:
                af, annale = diff.ids
                print(
                    f"\n--- AfQuestion ID: {af.question_id} | AnnaleQuestion ID: {annale.question_id} ---"
                )
                af_diff, annale_diff = colored_diff_lines(af.content, annale.content)
                print("af:     |", af_diff)
                print("annale  |", annale_diff)


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    engine = create_engine()
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "check_identicals": check_identicals,
    }
    run_subparser = subparsers.add_parser("run", help="Run a command")
    run_subparser.add_argument(
        "command",
        choices=commands.keys(),
        help="Command to run",
    )
    run_subparser.set_defaults(func=lambda args: commands[args.command](engine))
    # sub parser for compute_diffs
    diff_subparser = subparsers.add_parser(
        "show_diffs", help="Compute diffs between AnnaleQuestion and AfQuestion"
    )
    diff_subparser.add_argument(
        "--leven",
        type=int,
        default=3,
        help="Minimum Levenshtein distance to show diffs for",
    )
    diff_subparser.set_defaults(func=lambda args: sub_show_diffs(engine, args.leven))
    args = parser.parse_args()
    args.func(args)


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
