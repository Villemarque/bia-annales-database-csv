#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

""""""

from __future__ import annotations


import sqlmodel

from datetime import datetime, date, timezone
from typing import Optional

from log import SCRIPT_DIR, log
from sqlmodel import Field, SQLModel


class QuestionId(SQLModel, table=True):
    question_id: str = Field(primary_key=True)  # Explicitly mark as primary key
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checked_at: Optional[datetime] = None  # When the question was populated


def cleaned_str(s: str) -> str:
    """Return the string with normalized whitespace."""
    no_multi_space_lowered = " ".join(s.split()).lower()
    no_special = no_multi_space_lowered.translate(str.maketrans("", "", "'‘’«»“”„"))
    return no_special


# should be plenty of space for a ~1k question
def gen_unique_id() -> str:
    import secrets
    import string

    key_length = 8
    alphabet = string.ascii_letters + string.digits  # e.g., A-Z, a-z, 0-9
    return "".join(secrets.choice(alphabet) for _ in range(key_length))


class AnnaleToAfMapping(SQLModel, table=True):
    annale_question_id: str = Field(primary_key=True)
    af_question_id: str = Field(index=True)
    is_same: Optional[bool] = None  # None = unchecked, True = same, False = different
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AfQuestion(SQLModel, table=True):
    __tablename__ = "question"  # type: ignore[assignment]
    question_id: str = Field(primary_key=True)  # Explicitly mark as primary key
    content: str = Field(max_length=1024)  # Optional description
    choice_a: str = Field(min_length=1, nullable=False)
    choice_b: str = Field(min_length=1, nullable=False)
    choice_c: str = Field(min_length=1, nullable=False)
    choice_d: str = Field(min_length=1, nullable=False)
    answer: int = Field(min_length=1, max_length=1, nullable=False)  # 0, 1, 2, 3
    date_added: date
    chapter: str = Field(min_length=1, max_length=8, nullable=False)
    attachment_link: Optional[str] = Field(default=None, max_length=256)
    mixed_choices: bool

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def clean_content(self) -> str:
        return cleaned_str(self.content)

    def merge_chapter(self, other: AfQuestion) -> None:
        """Merge fields from other into self if they are None in self."""
        if self.chapter is None or len(other.chapter) > len(self.chapter):
            self.chapter = other.chapter


class ConsolidatedQuestion(SQLModel, table=True):
    qid: str = Field(primary_key=True)
    year: int = Field(nullable=False)
    label: str = Field(nullable=False)  # 1.1, 2.3, etc F.XX for English
    no: int = Field(nullable=False)  # 0-based in the year
    content_verbatim: str = Field(max_length=1024, nullable=False)
    content_fixed: Optional[str] = Field(max_length=1024)
    choice_a: str = Field(min_length=1, nullable=False)
    choice_b: str = Field(min_length=1, nullable=False)
    choice_c: str = Field(min_length=1, nullable=False)
    choice_d: str = Field(min_length=1, nullable=False)
    answer: int = Field(min_length=1, max_length=1, nullable=False)  # 0, 1, 2, 3
    chapter: Optional[str] = Field(min_length=1, max_length=8)
    attachment_link: Optional[str] = Field(default=None, max_length=256)
    mixed_choices: Optional[bool] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnnaleQuestion(SQLModel, table=True):
    question_id: str = Field(primary_key=True)  # year-question_number
    year: int = Field()
    question_number: str = Field()
    content: str = Field(max_length=1024)  # Optional description
    choice_a: str = Field(min_length=1, nullable=False)
    choice_b: str = Field(min_length=1, nullable=False)
    choice_c: str = Field(min_length=1, nullable=False)
    choice_d: str = Field(min_length=1, nullable=False)
    answer: int = Field(min_length=1, max_length=1, nullable=False)  # 0, 1, 2, 3
    attachment_link: Optional[str] = Field(default=None, max_length=256)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def clean_content(self) -> str:
        return cleaned_str(self.content)


class PdfQuestion(SQLModel, table=True):
    question_id: str = Field(primary_key=True)  # year-question_number
    year: int = Field()
    question_number: str = Field()
    content: str = Field(max_length=1024)  # Optional description
    choice_a: str = Field(min_length=1, nullable=False)
    choice_b: str = Field(min_length=1, nullable=False)
    choice_c: str = Field(min_length=1, nullable=False)
    choice_d: str = Field(min_length=1, nullable=False)
    attachment: bool = Field(default=False)
    answer: Optional[int] = Field(min_length=1, max_length=1)  # 0, 1, 2, 3
    has_issue: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def clean_content(self) -> str:
        return cleaned_str(self.content)


def create_engine():
    engine = sqlmodel.create_engine(f"sqlite:///{SCRIPT_DIR.parent}/questions.db")
    SQLModel.metadata.create_all(engine)
    if engine.url.database:
        log.info(f"Connected to database at {engine.url.database}")
    return engine
