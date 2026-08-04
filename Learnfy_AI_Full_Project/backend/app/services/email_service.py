"""SMTP email delivery with a safe local-development logging fallback."""
import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

from app.config.settings import settings

logger = logging.getLogger("learnfy_ai.email")


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        logger.warning("SMTP is not configured; email was not sent to %s", to_email)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Email delivery failed for %s", to_email)
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

