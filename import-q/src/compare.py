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
import diskcache
from sqlmodel import Session, select

from models import Question, AnnaleQuestion, create_engine
from log import log, SCRIPT_DIR

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

@dataclass(frozen=True)
class Diff:
    ids: Tuple[Question, AnnaleQuestion]
    leven_dist: int

    @classmethod
    def new(cls, af: Question, annale: AnnaleQuestion) -> Diff:
        return cls(
            ids=(af, annale),
            leven_dist=Levenshtein.distance(annale.content.strip().lower(), af.content.strip().lower())
            )


def check_identicals(engine) -> None:
    with Session(engine) as session: 
        annales = session.exec(select(AnnaleQuestion)).all()
        afs = session.exec(select(Question)).all()
        # diff by levenstein distance
        res: dict[int, list[Diff]] = {}
        assert len(afs) <= len(annales)
        for annale in annales: # it's important to have af in outer loop as they're fewer of them
            min_diff: Diff | None = None
            for af in afs:
                diff = Diff.new(af, annale)
                min_diff = min(diff, min_diff or diff, key=lambda d: d.leven_dist)
            assert min_diff is not None
            previous = res.get(min_diff.leven_dist, [])
            previous.append(min_diff)
            res[min_diff.leven_dist] = previous # in case it was not previously set
        
        for k in sorted(res.keys()):
            print(f"levenshtein distance: {k}, number of questions {len(res[k])}")

def main() -> None:
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    commands = {
        "check_identicals": check_identicals,
    }
    parser.add_argument("command", choices=commands.keys())
    engine = create_engine()
    args = parser.parse_args()
    commands[args.command](engine)



########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
