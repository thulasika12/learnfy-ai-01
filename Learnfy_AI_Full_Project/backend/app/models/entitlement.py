"""Subscription provider state, webhook idempotency, and daily AI usage."""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from app.config.database import Base

class DailyAIUsage(Base):
    __tablename__ = "daily_ai_usage"
    __table_args__ = (UniqueConstraint("user_id", "feature", "usage_date", name="uq_daily_ai_usage"),
                      Index("idx_daily_ai_usage_user_date", "user_id", "usage_date"))
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(30), nullable=False)
    usage_date = Column(Date, nullable=False)
    usage_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class StripeEvent(Base):
    __tablename__ = "stripe_events"
    event_id = Column(String(255), primary_key=True)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
