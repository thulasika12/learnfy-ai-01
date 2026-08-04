"""
Shared Gemini client used by all Learnfy AI feature modules.
"""

import logging
import time

from fastapi import HTTPException
from google import genai
from google.genai import types

from app.config.settings import settings


_client: genai.Client | None = None
logger = logging.getLogger("learnfy_ai.gemini")


def get_gemini_client() -> genai.Client:
    global _client

    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key.upper().startswith(("PASTE_", "YOUR_", "CHANGE_")):
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini API key is not configured. "
                "Set GEMINI_API_KEY in backend/.env and restart the server."
            ),
        )

    if _client is None:
        _client = genai.Client(api_key=api_key)

    return _client


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
) -> str:
    if not user_prompt or not user_prompt.strip():
        raise HTTPException(
            status_code=422,
            detail="AI prompt cannot be empty.",
        )

    client = get_gemini_client()

    max_attempts = 4
    wait_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_prompt.strip(),
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt.strip(),
                    temperature=temperature,
                ),
            )

            text = (response.text or "").strip()

            if not text:
                raise HTTPException(
                    status_code=502,
                    detail="Gemini returned an empty response.",
                )

            return text

        except HTTPException:
            raise

        except Exception as exc:
            message = str(exc)

            logger.warning(
                "Gemini request failed on attempt %s/%s: %s",
                attempt,
                max_attempts,
                type(exc).__name__,
            )

            is_temporary_error = (
                "503" in message
                or "429" in message
                or "UNAVAILABLE" in message
                or "RESOURCE_EXHAUSTED" in message
                or "high demand" in message.lower()
            )

            if is_temporary_error and attempt < max_attempts:
                logger.info("Gemini is busy; retrying in %s seconds", wait_seconds)
                time.sleep(wait_seconds)
                wait_seconds *= 2
                continue

            if (
                "API_KEY_INVALID" in message
                or "API key not valid" in message
            ):
                detail = (
                    "Invalid Gemini API key. "
                    "Create a new API key in Google AI Studio."
                )

            elif (
                "RESOURCE_EXHAUSTED" in message
                or "429" in message
            ):
                detail = (
                    "Gemini API quota has been reached. "
                    "Please wait and try again."
                )

            elif is_temporary_error:
                detail = (
                    "Gemini server is currently busy. "
                    "The request was retried several times. "
                    "Please try again after a few minutes."
                )

            elif (
                "404" in message
                or "not found" in message.lower()
            ):
                detail = (
                    f"Gemini model "
                    f"'{settings.GEMINI_MODEL}' is unavailable."
                )

            else:
                detail = "Gemini could not process the request. Please try again."

            raise HTTPException(
                status_code=502,
                detail=detail,
            ) from exc

    raise HTTPException(
        status_code=502,
        detail="Gemini could not generate a response.",
    )
