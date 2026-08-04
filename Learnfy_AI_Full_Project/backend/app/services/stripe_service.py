"""Stripe plan pricing and Checkout helpers."""
from dataclasses import dataclass
from decimal import Decimal

import stripe
from fastapi import HTTPException

from app.config.settings import settings


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    amount: Decimal
    duration_days: int | None
    features: tuple[str, ...]


PLANS = {
    "free": Plan("free", "Free", Decimal("0.00"), None, ("Notes and community", "Basic learning tools")),
    "monthly": Plan(
        "monthly", "Monthly Premium", Decimal("500.00"), 30,
        ("All AI learning tools", "Premium access for 30 days", "Priority learning experience"),
    ),
    "yearly": Plan(
        "yearly", "Yearly Premium", Decimal("5000.00"), 365,
        ("All AI learning tools", "Premium access for 365 days", "Save LKR 1,000 per year"),
    ),
}


def validate_checkout_configuration() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe checkout is not configured: set STRIPE_SECRET_KEY in backend/.env",
        )


def validate_webhook_configuration() -> None:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Stripe webhooks are not configured: set STRIPE_WEBHOOK_SECRET in backend/.env",
        )


def amount_in_smallest_unit(amount: Decimal) -> int:
    return int(amount * 100)


def configure_stripe() -> None:
    stripe.api_key = settings.STRIPE_SECRET_KEY
