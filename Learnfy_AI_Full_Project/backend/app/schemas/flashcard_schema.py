"""Validated flashcard generation, persistence, study, sharing, and reminder contracts."""
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Language = Literal["en", "ta", "si"]
Difficulty = Literal["easy", "medium", "hard"]
SourceType = Literal["topic", "text", "pdf", "document", "note"]


class GeneratedCard(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    answer: str = Field(min_length=1, max_length=5000)
    image_suggestion: str | None = Field(default=None, max_length=500)


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    subject: str = Field(default="Other", min_length=2, max_length=100)
    count: int = Field(default=10, ge=1, le=30)
    difficulty: Difficulty = "medium"
    language: Language = "en"
    grade: str = Field(min_length=1, max_length=50)
    medium: Language


class GenerateFromTextRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    subject: str = Field(default="Other", min_length=2, max_length=100)
    text: str = Field(min_length=20, max_length=100000)
    count: int = Field(default=10, ge=1, le=30)
    difficulty: Difficulty = "medium"
    language: Language = "en"
    grade: str = Field(min_length=1, max_length=50)
    medium: Language


class GenerateFromNoteRequest(BaseModel):
    note_id: int = Field(gt=0)
    count: int = Field(default=10, ge=1, le=30)
    difficulty: Difficulty = "medium"
    language: Language = "en"


class GeneratedSet(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    subject: str = Field(min_length=2, max_length=100)
    language: Language
    difficulty: Difficulty
    source_type: SourceType
    source_name: str | None = None
    cards: list[GeneratedCard] = Field(min_length=1, max_length=30)


class CardCreate(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    answer: str = Field(min_length=1, max_length=5000)
    image_url: str | None = Field(default=None, max_length=500)
    is_favourite: bool = False


class SetCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    subject: str = Field(min_length=2, max_length=100)
    source_type: SourceType = "topic"
    source_name: str | None = Field(default=None, max_length=255)
    language: Language = "en"
    difficulty: Difficulty = "medium"
    cards: list[CardCreate] = Field(min_length=1, max_length=30)


class SetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    subject: str | None = Field(default=None, min_length=2, max_length=100)
    cards: list[CardCreate] | None = Field(default=None, min_length=1, max_length=30)


class CardOut(CardCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sort_order: int


class SetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    subject: str
    source_type: str
    source_name: str | None
    language: str
    difficulty: str
    is_favourite: bool
    is_public: bool
    share_token: str | None
    share_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    cards: list[CardOut]
    best_score: float | None = None


class SessionAnswerIn(BaseModel):
    card_id: int
    status: Literal["known", "review"]


class StudySessionCreate(BaseModel):
    duration_seconds: int = Field(ge=0, le=86400)
    answers: list[SessionAnswerIn] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def unique_cards(self):
        if len({item.card_id for item in self.answers}) != len(self.answers):
            raise ValueError("Each card may be answered only once")
        return self


class StudySessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    correct_count: int
    incorrect_count: int
    total_cards: int
    score_percentage: float
    duration_seconds: int
    completed_at: datetime


class ShareRequest(BaseModel):
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class ShareOut(BaseModel):
    share_token: str
    share_url: str
    expires_at: datetime | None


class ReminderUpdate(BaseModel):
    is_enabled: bool
    reminder_time: time
    timezone: str = Field(min_length=1, max_length=80)


class ReminderOut(ReminderUpdate):
    model_config = ConfigDict(from_attributes=True)
    last_notified_at: datetime | None = None


class DashboardStats(BaseModel):
    total_sets: int
    total_cards_studied: int
    average_score: float
    revision_streak: int
