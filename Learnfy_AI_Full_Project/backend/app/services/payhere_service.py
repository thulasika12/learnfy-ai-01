"""PayHere Checkout hashing and configuration. Merchant secrets never leave this module."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
from urllib.parse import urlparse

from fastapi import HTTPException
from app.config.settings import settings

SANDBOX_CHECKOUT = "https://sandbox.payhere.lk/pay/checkout"
PRODUCTION_CHECKOUT = "https://www.payhere.lk/pay/checkout"

@dataclass(frozen=True)
class PayHerePlan:
    code: str
    name: str
    amount: Decimal
    duration_days: int
    features: tuple[str, ...]

def plans() -> dict[str, PayHerePlan]:
    try:
        amount_30 = Decimal(settings.PAYHERE_30_DAY_AMOUNT).quantize(Decimal("0.01"))
        amount_365 = Decimal(settings.PAYHERE_365_DAY_AMOUNT).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise RuntimeError("PayHere plan amounts must be valid decimals") from exc
    return {
        "premium_30_days": PayHerePlan("premium_30_days", "30-Day Premium Access", amount_30, 30,
            ("All AI learning tools", "Premium access for 30 days", "Manual renewal")),
        "premium_365_days": PayHerePlan("premium_365_days", "365-Day Premium Access", amount_365, 365,
            ("All AI learning tools", "Premium access for 365 days", "Manual renewal")),
    }

def amount_text(value: Decimal | str) -> str:
    return f"{Decimal(str(value)):.2f}"

def _md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest().upper()

def checkout_hash(merchant_id: str, order_id: str, amount: Decimal | str, currency: str, secret: str) -> str:
    return _md5(f"{merchant_id}{order_id}{amount_text(amount)}{currency}{_md5(secret)}")

def notification_signature(merchant_id: str, order_id: str, amount: str, currency: str,
                           status_code: str, secret: str) -> str:
    return _md5(f"{merchant_id}{order_id}{amount}{currency}{status_code}{_md5(secret)}")

def valid_notification_signature(received: str, **values) -> bool:
    expected = notification_signature(secret=settings.PAYHERE_MERCHANT_SECRET, **values)
    return hmac.compare_digest(expected, (received or "").upper())

def configuration() -> tuple[bool, str]:
    if not settings.PAYHERE_ENABLED:
        return False, "Payments are currently unavailable"
    if settings.PAYMENT_PROVIDER != "payhere":
        return False, "PayHere is not the selected payment provider"
    credentials = (settings.PAYHERE_MERCHANT_ID.strip(), settings.PAYHERE_MERCHANT_SECRET.strip())
    if not all(credentials) or any(value.lower().startswith(("your_", "change", "replace", "example")) for value in credentials):
        return False, "PayHere merchant credentials are not configured"
    public = urlparse(settings.BACKEND_PUBLIC_URL)
    if public.scheme != "https" or not public.netloc:
        return False, "PayHere requires a public HTTPS backend URL for notifications"
    if settings.PAYHERE_CURRENCY.upper() != "LKR":
        return False, "PayHere currency must be LKR"
    frontend = urlparse(settings.FRONTEND_URL)
    if not settings.PAYHERE_SANDBOX and (frontend.scheme != "https" or not frontend.netloc):
        return False, "PayHere Production requires an HTTPS frontend URL"
    return True, "PayHere Sandbox is configured" if settings.PAYHERE_SANDBOX else "PayHere Production is configured"

def require_configuration() -> None:
    enabled, message = configuration()
    if not enabled:
        raise HTTPException(503, message)

def checkout_url() -> str:
    return SANDBOX_CHECKOUT if settings.PAYHERE_SANDBOX else PRODUCTION_CHECKOUT
