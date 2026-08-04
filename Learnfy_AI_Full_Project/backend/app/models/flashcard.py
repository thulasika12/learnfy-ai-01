"""Private flashcard sets, cards, study history, sharing, and reminders."""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class FlashcardSet(Base):
    __tablename__ = "flashcard_sets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    source_type = Column(String(30), nullable=False, default="topic")
    source_name = Column(String(255))
    language = Column(String(5), nullable=False, default="en")
    difficulty = Column(String(20), nullable=False, default="medium")
    is_favourite = Column(Boolean, nullable=False, default=False, index=True)
    is_public = Column(Boolean, nullable=False, default=False)
    share_token = Column(String(100), unique=True, index=True)
    share_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="flashcard_sets")
    cards = relationship("Flashcard", back_populates="set", cascade="all, delete-orphan", order_by="Flashcard.sort_order")
    study_sessions = relationship("FlashcardStudySession", back_populates="set", cascade="all, delete-orphan")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey("flashcard_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    image_url = Column(String(500))
    is_favourite = Column(Boolean, nullable=False, default=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    set = relationship("FlashcardSet", back_populates="cards")
    session_answers = relationship("FlashcardSessionAnswer", back_populates="card", cascade="all, delete-orphan")


class FlashcardStudySession(Base):
    __tablename__ = "flashcard_study_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    set_id = Column(Integer, ForeignKey("flashcard_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    correct_count = Column(Integer, nullable=False)
    incorrect_count = Column(Integer, nullable=False)
    total_cards = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="flashcard_study_sessions")
    set = relationship("FlashcardSet", back_populates="study_sessions")
    answers = relationship("FlashcardSessionAnswer", back_populates="session", cascade="all, delete-orphan")


class FlashcardSessionAnswer(Base):
    __tablename__ = "flashcard_session_answers"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("flashcard_study_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("FlashcardStudySession", back_populates="answers")
    card = relationship("Flashcard", back_populates="session_answers")


class FlashcardReminder(Base):
    __tablename__ = "flashcard_reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_enabled = Column(Boolean, nullable=False, default=False)
    reminder_time = Column(Time, nullable=False)
    timezone = Column(String(80), nullable=False, default="UTC")
    last_notified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="flashcard_reminder")
