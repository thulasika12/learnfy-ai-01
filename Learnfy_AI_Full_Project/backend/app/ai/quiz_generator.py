"""
AI Quiz Generator — produces MCQ questions from a subject/topic, or from
supplied source text (e.g. a note's content), returned as strict JSON.
"""
import json
import re
from typing import List, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.ai_schema import GeneratedQuizQuestion
from app.services.ai_service import chat_completion

SYSTEM_PROMPT = (
    "You are an expert exam question setter. Generate multiple-choice questions (MCQs) "
    "strictly as a JSON array and nothing else — no markdown, no commentary, no code fences. "
    "Each item must have exactly this shape: "
    '{"question": "string", "options": ["A", "B", "C", "D"], "answer": "the correct option text"}. '
    "Options must be plausible and only one should be correct."
)


LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "si": "Sinhala",
}


def _parse_questions(raw: str, expected_count: int) -> List[dict]:
    cleaned = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("response was not valid JSON") from exc

    if not isinstance(payload, list):
        raise ValueError("response must be a JSON array")
    if len(payload) != expected_count:
        raise ValueError(f"expected {expected_count} questions but received {len(payload)}")

    try:
        return [GeneratedQuizQuestion.model_validate(item).model_dump() for item in payload]
    except ValidationError as exc:
        raise ValueError("one or more questions failed schema validation") from exc


def generate_quiz(
    subject: str,
    topic: str,
    num_questions: int = 5,
    source_text: Optional[str] = None,
    language: str = "en",
    difficulty: str = "medium",
    grade: str = "A/L",
    medium: str = "en",
) -> List[dict]:
    output_language = LANGUAGE_NAMES.get(language, "English")
    if source_text:
        user_prompt = (
            f"Generate {num_questions} MCQ questions about the subject '{subject}', topic '{topic}', "
            f"based strictly on the following study material. Write every question and option in "
            f"{output_language} at {difficulty} difficulty for {grade} in {medium} learning medium. Keep content strictly appropriate to that grade. Keep the JSON property names in English.\n\n{source_text}"
        )
    else:
        user_prompt = (
            f"Generate {num_questions} MCQ questions for the subject '{subject}' on the topic '{topic}', "
            f"suitable for a student revising this topic. Write every question and option in "
            f"{output_language} at {difficulty} difficulty for {grade} in {medium} learning medium. Keep content strictly appropriate to that grade. Keep the JSON property names in English."
        )

    last_error = None
    for attempt in range(2):
        prompt = user_prompt
        if attempt:
            prompt += (
                "\n\nYour previous response was invalid. Return exactly the requested number "
                "of questions as a bare JSON array matching the required schema."
            )
        raw = chat_completion(SYSTEM_PROMPT, prompt, temperature=0.4)
        try:
            return _parse_questions(raw, num_questions)
        except ValueError as exc:
            last_error = exc

    raise HTTPException(
        status_code=502,
        detail="The AI returned invalid quiz content after two attempts. Please try again.",
    ) from last_error
