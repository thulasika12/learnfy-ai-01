"""API contracts for Stripe checkout and subscription data."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlanOut(BaseModel):
    code: str
    name: str
    amount: Decimal
    currency: str
    duration_days: int | None
    features: list[str]


class CheckoutRequest(BaseModel):
    plan_code: Literal["monthly", "yearly"]

class PayHereOrderRequest(BaseModel):
    plan_code: Literal["premium_30_days", "premium_365_days"]
    phone: str = Field(min_length=7, max_length=30)
    address: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=2, max_length=100)

class PayHereOrderResponse(BaseModel):
    order_id: str
    provider: Literal["payhere"] = "payhere"
    checkout_url: str
    fields: dict[str, str]


class CheckoutResponse(BaseModel):
    order_id: str
    provider: str
    checkout_url: str


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: str
    provider: str
    provider_payment_id: str | None
    plan_code: str
    amount: Decimal
    currency: str
    status: str
    payment_method: str | None
    status_message: str | None
    paid_at: datetime | None
    created_at: datetime


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    plan_code: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False


class PaymentStatusOut(BaseModel):
    payment: PaymentOut
    subscription: SubscriptionOut | None = None


class MyPaymentsOut(BaseModel):
    plan_code: str
    is_premium: bool
    subscription: SubscriptionOut | None
    payments: list[PaymentOut]


class AdminPaymentOut(PaymentOut):
    user_id: int
    user_name: str
    user_email: str
    subscription_expires_at: datetime | None = None
