"""Central A/L subject catalogue with reusable stream mappings."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.config.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("level", "subject_code", name="uq_subject_level_code"),)
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False, default="AL", index=True)
    stream = Column(String(100), nullable=False)
    subject_code = Column(String(10), nullable=False)
    name_en = Column(String(255), nullable=False)
    name_ta = Column(String(255), nullable=False)
    name_si = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stream_links = relationship("SubjectStream", back_populates="subject", cascade="all, delete-orphan")
    grade_links = relationship("GradeSubject", back_populates="subject", cascade="all, delete-orphan")

class SubjectStream(Base):
    __tablename__ = "subject_streams"
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)
    stream = Column(String(100), primary_key=True)
    subject = relationship("Subject", back_populates="stream_links")
