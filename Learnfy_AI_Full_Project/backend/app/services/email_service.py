"""Transactional email delivery through the Resend HTTPS API."""
from html import escape
import logging
from urllib.parse import urlencode

import httpx

from app.config.settings import settings

logger = logging.getLogger("learnfy_ai.email")


def _send_email(to_email: str, subject: str, body: str) -> bool:
    api_key = settings.RESEND_API_KEY.strip()
    if not api_key:
        logger.warning("Resend is not configured; email was not sent")
        return False

    html_body = f'<div style="white-space: pre-wrap">{escape(body)}</div>'

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": settings.EMAIL_FROM, "to": [to_email], "subject": subject, "html": html_body},
            timeout=20.0,
        )
        if not response.is_success:
            logger.error(
                "Resend delivery failed with status %s (request_id=%s)",
                response.status_code,
                response.headers.get("x-request-id", "unavailable"),
            )
            return False
        return True
    except httpx.HTTPError as exc:
        logger.error("Resend delivery failed due to %s", type(exc).__name__)
        return False


def send_password_reset_email(to_email: str, reset_token: str):
    query = urlencode({"email": to_email, "token": reset_token})
    reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?{query}"
    return _send_email(
        to_email,
        "Reset your Learnfy AI password",
        f"Use this secure link to reset your password:\n\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email.",
    )


def send_email_verification_code(to_email: str, code: str):
    return _send_email(
        to_email,
        "Verify your Learnfy AI email",
        f"Your Learnfy AI verification code is {code}. It expires in 15 minutes.\n\n"
        "If you did not create this account, you can ignore this email.",
    )
