"""Payment and Premium subscription records."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(64), nullable=False, unique=True, index=True)
    provider = Column(String(30), nullable=False, default="stripe")
    provider_payment_id = Column(String(100), nullable=True, unique=True, index=True)
    plan_code = Column(String(30), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="LKR")
    status = Column(String(30), nullable=False, default="initiated", index=True)
    payment_method = Column(String(50), nullable=True)
    status_message = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="source_payment", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_code = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="active", index=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    source_payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, unique=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="subscriptions")
    source_payment = relationship("Payment", back_populates="subscription")
