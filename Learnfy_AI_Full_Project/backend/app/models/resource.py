"""
Resource model — educational resources / study materials uploaded by teachers.
Separate from student Notes so teacher-curated material can be surfaced
differently in the UI.
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=False)
    grade = Column(String(50), nullable=True, index=True)
    stream = Column(String(100), nullable=True)
    medium = Column(String(10), nullable=True)
    file_url = Column(String(500), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User")
