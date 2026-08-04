"""
AI Quiz Generator — produces MCQ questions from a subject/topic, or from
supplied source text (e.g. a note's content), returned as strict JSON.
"""
import json
from typing import List, Optional

from fastapi import HTTPException

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

    raw = chat_completion(SYSTEM_PROMPT, user_prompt, temperature=0.4)

    # Defensive parsing in case the model wraps JSON in code fences
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        questions = json.loads(cleaned)
        if not isinstance(questions, list) or not questions:
            raise ValueError("Expected a JSON array")
        validated = []
        for item in questions[:num_questions]:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            options = item.get("options")
            answer = str(item.get("answer", "")).strip()
            normalized_options = [str(option).strip() for option in options] if isinstance(options, list) else []
            if (
                question
                and isinstance(options, list)
                and len(options) == 4
                and all(normalized_options)
                and len(set(normalized_options)) == 4
                and answer in normalized_options
            ):
                validated.append(
                    {
                        "question": question,
                        "options": normalized_options,
                        "answer": answer,
                    }
                )
        if len(validated) != num_questions:
            raise ValueError(f"Expected {num_questions} valid questions but received {len(validated)}")
        return validated
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned an unexpected format: {exc}") from exc
