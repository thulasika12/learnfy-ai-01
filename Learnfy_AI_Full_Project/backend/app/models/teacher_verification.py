"""Audited teacher privilege applications with private proof documents."""
import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship
from app.config.database import Base

class VerificationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class TeacherVerification(Base):
    __tablename__ = "teacher_verifications"
    __table_args__ = (Index("idx_teacher_verifications_status_submitted", "status", "submitted_at"), Index("idx_teacher_verifications_user", "user_id"))
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(150), nullable=False)
    qualification = Column(String(255), nullable=True)
    institution_name = Column(String(255), nullable=False)
    subjects_taught = Column(Text, nullable=False)
    grades_taught = Column(Text, nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    official_email = Column(String(150))
    proof_file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    additional_information = Column(Text)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.pending)
    rejection_reason = Column(Text)
    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    applicant = relationship("User", foreign_keys=[user_id], back_populates="teacher_verifications")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
