"""
User model. Roles: student, teacher, admin.
"""
import enum

from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class StudentVerificationStatus(str, enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # hashed
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    profile_image = Column(String(500), nullable=True)
    bio = Column(String(500), nullable=True)
    academic_level = Column(String(20), nullable=True)
    academic_stream = Column(String(100), nullable=True)
    academic_subject = Column(String(255), nullable=True)
    is_verified_teacher = Column(Boolean, default=False)
    # Compatibility default for trusted/admin-created records; public registration explicitly sets False.
    is_email_verified = Column(Boolean, nullable=False, default=True)
    student_verification_status = Column(Enum(StudentVerificationStatus), nullable=False, default=StudentVerificationStatus.unverified)
    student_verified_at = Column(DateTime(timezone=True), nullable=True)
    student_verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deletion_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    notes = relationship("Note", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    groups_created = relationship("StudyGroup", back_populates="creator", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    group_join_requests = relationship(
        "GroupJoinRequest", back_populates="user", cascade="all, delete-orphan"
    )
    ai_chats = relationship("AIChat", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    flashcard_sets = relationship("FlashcardSet", back_populates="user", cascade="all, delete-orphan")
    flashcard_study_sessions = relationship("FlashcardStudySession", back_populates="user", cascade="all, delete-orphan")
    flashcard_reminder = relationship("FlashcardReminder", back_populates="user", cascade="all, delete-orphan", uselist=False)
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    academic_profile = relationship("UserAcademicProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    teacher_verifications = relationship("TeacherVerification", foreign_keys="TeacherVerification.user_id", back_populates="applicant", cascade="all, delete-orphan")
    student_verifications = relationship("StudentVerification", foreign_keys="StudentVerification.user_id", back_populates="applicant", cascade="all, delete-orphan")
