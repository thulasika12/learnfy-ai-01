"""User-submitted reports for administratively moderated content."""
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class ReportStatus(str, enum.Enum):
    pending = "pending"
    dismissed = "dismissed"
    hidden = "hidden"
    deleted = "deleted"


class ContentReport(Base):
    __tablename__ = "content_reports"
    __table_args__ = (
        Index("idx_content_reports_status_created", "status", "created_at"),
        Index("idx_content_reports_target", "target_type", "target_id"),
    )

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type = Column(String(30), nullable=False)
    target_id = Column(Integer, nullable=False)
    reason = Column(String(1000), nullable=False)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.pending)
    resolution_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reporter = relationship("User", foreign_keys=[reporter_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
