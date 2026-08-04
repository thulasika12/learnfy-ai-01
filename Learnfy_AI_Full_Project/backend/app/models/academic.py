"""Normalized Sri Lankan education structure and user academic mappings."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.config.database import Base

class EducationLevel(Base):
    __tablename__ = "education_levels"
    id = Column(Integer, primary_key=True); code = Column(String(30), unique=True, nullable=False)
    name_en = Column(String(100), nullable=False); name_ta = Column(String(100), nullable=False); name_si = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0); is_active = Column(Boolean, default=True)

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True); level_id = Column(Integer, ForeignKey("education_levels.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(30), unique=True, nullable=False); name_en = Column(String(100), nullable=False); name_ta = Column(String(100), nullable=False); name_si = Column(String(100), nullable=False)
    grade_number = Column(Integer); sort_order = Column(Integer, default=0); is_active = Column(Boolean, default=True)
    level = relationship("EducationLevel")

class AcademicStream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True); code = Column(String(50), unique=True, nullable=False)
    name_en = Column(String(100), nullable=False); name_ta = Column(String(100), nullable=False); name_si = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True); sort_order = Column(Integer, default=0)

class GradeSubject(Base):
    __tablename__ = "grade_subjects"
    __table_args__ = (UniqueConstraint("grade_id", "subject_id", "medium", name="uq_grade_subject_medium"),)
    id = Column(Integer, primary_key=True); grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False); medium = Column(String(10), nullable=False, default="all")
    sort_order = Column(Integer, default=0); is_active = Column(Boolean, default=True)
    grade = relationship("Grade"); subject = relationship("Subject", back_populates="grade_links")

class UserAcademicProfile(Base):
    __tablename__ = "user_academic_profiles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    education_level_id = Column(Integer, ForeignKey("education_levels.id")); grade_id = Column(Integer, ForeignKey("grades.id")); stream_id = Column(Integer, ForeignKey("streams.id"))
    medium = Column(String(10)); school_name = Column(String(255)); district = Column(String(100)); guardian_consent = Column(Boolean, default=False)
    user = relationship("User", back_populates="academic_profile"); education_level = relationship("EducationLevel"); grade = relationship("Grade"); stream = relationship("AcademicStream")

class UserSubject(Base):
    __tablename__ = "user_subjects"; user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True); subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)
class TeacherGrade(Base):
    __tablename__ = "teacher_grades"; user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True); grade_id = Column(Integer, ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True)
class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"; user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True); subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)
