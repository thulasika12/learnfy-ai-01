"""
Quiz model — stores AI-generated MCQ questions.
`options` is stored as a JSON-encoded string, e.g. '["A","B","C","D"]'.
"""
from sqlalchemy import Column, Integer, Text, String, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"
    __table_args__ = (Index("idx_quizzes_batch_owner", "quiz_batch_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(100), nullable=True)
    topic = Column(String(255), nullable=True)
    grade = Column(String(50), nullable=True, index=True)
    medium = Column(String(10), nullable=True)
    difficulty = Column(String(20), nullable=False, default="medium")
    language = Column(String(5), nullable=False, default="en")
    quiz_batch_id = Column(String(36), nullable=True)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON string list of options
    answer = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="quizzes")
