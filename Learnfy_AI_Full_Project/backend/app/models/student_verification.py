"""Private student proof submissions with audited admin review."""
import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship
from app.config.database import Base

class StudentProofStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"

class StudentVerification(Base):
    __tablename__ = "student_verifications"
    __table_args__ = (Index("idx_student_verifications_status_submitted", "status", "submitted_at"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    proof_file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    status = Column(Enum(StudentProofStatus), nullable=False, default=StudentProofStatus.pending)
    rejection_reason = Column(Text)
    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    applicant = relationship("User", foreign_keys=[user_id], back_populates="student_verifications")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
