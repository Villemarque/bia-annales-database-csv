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


from sqlmodel import Field, SQLModel, Session, select

class QuestionId(SQLModel, table=True):
    question_id: str = Field(primary_key=True)  # Explicitly mark as primary key
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checked_at: Optional[datetime] = None  # When the question was populated


class Question(SQLModel, table=True):
    question_id: str = Field(primary_key=True)  # Explicitly mark as primary key
    content: str = Field(max_length=1024)  # Optional description
    choice_a: str = Field(min_length=1,nullable=False)
    choice_b: str = Field(min_length=1,nullable=False)
    choice_c: str = Field(min_length=1,nullable=False)
    choice_d: str = Field(min_length=1,nullable=False)
    answer: int = Field(min_length=1, max_length=1,nullable=False)  # 0, 1, 2, 3
    date_added: date
    chapter: str = Field(min_length=1,max_length=8,nullable=False)
    attachment_link: Optional[str] = Field(default=None, max_length=256)
    mixed_choices: bool

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
