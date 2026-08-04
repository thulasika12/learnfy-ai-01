"""
Pydantic schemas for the AI features: chat, summarizer, quiz generator,
and study planner.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    subject: Optional[str] = Field(default=None, max_length=255)
    grade: Optional[str] = Field(default=None, max_length=50)
    medium: Optional[Literal["en", "ta", "si"]] = None
    response_language: Literal["en", "ta", "si"] = "en"


class ChatResponse(BaseModel):
    question: str
    answer: str
    created_at: datetime


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=10)
    length: Optional[str] = Field(default="medium", description="short | medium | long")
    subject: Optional[str] = Field(default=None, max_length=255)
    grade: Optional[str] = Field(default=None, max_length=50)
    medium: Optional[Literal["en", "ta", "si"]] = None
    response_language: Literal["en", "ta", "si"] = "en"


class SummarizeResponse(BaseModel):
    summary: str


class QuizGenerateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=255)
    num_questions: int = Field(default=5, ge=1, le=20)
    source_text: Optional[str] = None
    language: Literal["en", "ta", "si"] = "en"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    grade: str = Field(min_length=1, max_length=50)
    medium: Literal["en", "ta", "si"]


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]


class QuizGenerateResponse(BaseModel):
    subject: str
    topic: str
    language: str
    difficulty: str
    questions: List[QuizQuestion]


class QuizAnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str = Field(min_length=1, max_length=500)


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswerSubmission] = Field(min_length=1, max_length=20)


class QuizQuestionReview(BaseModel):
    question_id: int
    question: str
    options: List[str]
    selected_answer: str
    correct_answer: str
    is_correct: bool


class QuizSubmitResponse(BaseModel):
    score: int
    total: int
    percentage: float
    review: List[QuizQuestionReview]


class StudyPlanRequest(BaseModel):
    subjects: List[str]
    hours_per_day: float = Field(default=2, ge=0.5, le=16)
    days: int = Field(default=7, ge=1, le=90)
    goal: Optional[str] = None
    grade: Optional[str] = Field(default=None, max_length=50)
    medium: Optional[Literal["en", "ta", "si"]] = None
    response_language: Literal["en", "ta", "si"] = "en"


class StudyPlanDay(BaseModel):
    day: int
    tasks: List[str]


class StudyPlanResponse(BaseModel):
    plan: List[StudyPlanDay]


class FlashcardGenerateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    count: int = Field(default=6, ge=3, le=20)


class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardGenerateResponse(BaseModel):
    topic: str
    cards: List[Flashcard]
