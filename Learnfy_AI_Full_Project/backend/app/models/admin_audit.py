"""Immutable audit entries for sensitive administrator actions."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from app.config.database import Base

class AdminAudit(Base):
    __tablename__="admin_audits"
    __table_args__=(Index("idx_admin_audits_actor_created","actor_id","created_at"),)
    id=Column(Integer,primary_key=True)
    actor_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    action=Column(String(100),nullable=False)
    target_type=Column(String(50),nullable=False)
    target_id=Column(Integer,nullable=True)
    details=Column(Text,nullable=True)
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
