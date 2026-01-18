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
from sqlmodel import Session, select

from models import AfQuestion, AnnaleQuestion, create_engine, PdfQuestion
from log import SCRIPT_DIR
from cache import CACHE

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


def compute_diffs_annale_af(
    engine,
) -> dict[int, list[Diff[AfQuestion, AnnaleQuestion]]]:
    with Session(engine) as session:
        a_s = session.exec(select(AfQuestion)).all()
        b_s = session.exec(select(AnnaleQuestion)).all()
        return compute_diffs(a_s, b_s)


def compute_diffs_annale_pdf(
    engine,
) -> dict[int, list[Diff[AnnaleQuestion, PdfQuestion]]]:
    with Session(engine) as session:
        a_s = session.exec(select(AnnaleQuestion)).all()
        b_s = session.exec(select(PdfQuestion)).all()
        return compute_diffs(a_s, b_s)


@CACHE.memoize(name="compute_diffs_v2")
def compute_diffs(
    a_s: Sequence[A],
    b_s: Sequence[B],
) -> dict[int, list[Diff]]:
    res: dict[int, list[Diff]] = {}
    assert len(a_s) <= len(b_s)
    for a in a_s:  # it's important to have af in outer loop as they're fewer of them
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


def show_diffs_pdf(engine) -> None:
    res = compute_diffs_annale_pdf(engine)
    print("\nShowing diffs between PDF and Annale:\n")
    for k in sorted(res.keys()):
        if k <= 3:
            continue
        print(
            f"\n\n=== Levenshtein distance: {k}, number of questions {len(res[k])} ==="
        )
        for diff in res[k]:
            t: Tuple[AnnaleQuestion, PdfQuestion] = diff.ids
            a, b = t
            print(
                f"\n--- AnnaleQuestion ID: {a.question_id} | PdfQuestion ID: {b.question_id} ---"
            )
            a_diff, b_diff = colored_diff_lines(a.content, b.content)
            print("annale:     |", a_diff)
            print("pdf:    |", b_diff)
            print("annale: ", a)
            print("pdf:    ", b)

    with Session(engine) as session:
        a_s = session.exec(select(AnnaleQuestion)).all()
        b_s = session.exec(select(PdfQuestion)).all()
    a_dict = {a.question_id: a for a in a_s}
    b_dict = {b.question_id: b for b in b_s}
    i = 0
    for a_id, a in a_dict.items():
        if b_dict[a_id].answer != a.answer:
            i += 1
            print(
                f"Answer mismatch for question ID {a_id}: Annale answer {a.answer}, PDF answer {b_dict[a_id].answer}"
            )
            print(a.content)
            print()
            print(a.choice_a)
            print(a.choice_b)
            print(a.choice_c)
            print(a.choice_d)
            print()

    # 440 missmtach with gemini-3-flash-preview
    # 336 missmtach with gemini-3-pro-preview
    print(f"\nTotal answer mismatches between Annale and PDF: {i}")


def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    engine = create_engine()
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "check_identicals": check_identicals,
        "show_diffs_pdf": show_diffs_pdf,
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
