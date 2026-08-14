from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.routes.auth import request_email_verification
from app.services.email_service import send_email_verification_code, send_password_reset_email


@patch("app.services.email_service.settings.RESEND_API_KEY", "re_test_key")
@patch("app.services.email_service.settings.EMAIL_FROM", "onboarding@resend.dev")
def test_verification_email_uses_resend_https_api():
    response = Mock(is_success=True, status_code=200, headers={})
    with patch("app.services.email_service.httpx.post", return_value=response) as post:
        assert send_email_verification_code("student@example.com", "123456") is True

    _, kwargs = post.call_args
    assert post.call_args.args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    assert kwargs["json"]["from"] == "onboarding@resend.dev"
    assert kwargs["json"]["to"] == ["student@example.com"]
    assert kwargs["json"]["subject"] == "Verify your Learnfy AI email"
    assert "123456" in kwargs["json"]["html"]


@patch("app.services.email_service.settings.RESEND_API_KEY", "re_test_key")
def test_password_reset_email_preserves_subject_and_link():
    response = Mock(is_success=True, status_code=200, headers={})
    with patch("app.services.email_service.httpx.post", return_value=response) as post:
        assert send_password_reset_email("student@example.com", "safe-token") is True

    payload = post.call_args.kwargs["json"]
    assert payload["subject"] == "Reset your Learnfy AI password"
    assert "reset-password?email=student%40example.com&amp;token=safe-token" in payload["html"]


@pytest.mark.parametrize(
    "post_result",
    [
        Mock(is_success=False, status_code=429, headers={"x-request-id": "safe-request-id"}),
        httpx.ConnectError("network unavailable"),
    ],
)
@patch("app.services.email_service.settings.RESEND_API_KEY", "re_test_key")
def test_resend_failure_returns_false(post_result):
    effect = post_result if isinstance(post_result, Exception) else None
    result = None if effect else post_result
    with patch("app.services.email_service.httpx.post", return_value=result, side_effect=effect):
        assert send_email_verification_code("student@example.com", "123456") is False


def test_verification_request_returns_502_when_delivery_fails():
    user = SimpleNamespace(id=1, is_email_verified=False)
    with patch("app.routes.auth.enforce"), patch("app.routes.auth.issue_email_code", return_value=False):
        with pytest.raises(HTTPException) as error:
            request_email_verification(request=None, db=None, user=user)
    assert error.value.status_code == 502
    assert "could not be delivered" in error.value.detail
