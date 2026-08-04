"""Generate and strictly validate structured study flashcards with Gemini."""
import json

from fastapi import HTTPException

from app.services.ai_service import chat_completion
from app.schemas.flashcard_schema import GeneratedSet

SYSTEM_PROMPT = """You are an expert teacher creating concise, factual educational flashcards.
Return valid JSON only, without markdown or commentary, using exactly this object shape:
{"title":"string","subject":"string","language":"en|ta|si","difficulty":"easy|medium|hard","cards":[{"question":"string","answer":"string","image_suggestion":null}]}
Avoid duplicate questions and empty answers. Preserve the requested language and difficulty.
When source material is supplied, use only facts explicitly present in that material. Never add outside facts.
Generate exactly the requested number of cards whenever the material contains enough distinct facts."""


def _parse_response(raw: str, expected_count: int, defaults: dict) -> GeneratedSet:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Response must be an object")
        data = {**data, **defaults}
        data["cards"] = data.get("cards", [])[:expected_count]
        result = GeneratedSet.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="AI returned an invalid flashcard format") from exc
    if not result.cards:
        raise HTTPException(status_code=502, detail="AI returned no usable flashcards")
    return result


def generate_flashcard_set(
    *, title: str, subject: str, count: int, difficulty: str, language: str,
    source_type: str = "topic", source_name: str | None = None, source_text: str | None = None,
    grade: str | None = None, medium: str | None = None,
) -> GeneratedSet:
    source_instruction = ""
    if source_text:
        source_instruction = (
            "\nUse ONLY the source material between SOURCE_START and SOURCE_END. "
            "If there are not enough distinct facts, return fewer cards rather than inventing content."
            f"\nSOURCE_START\n{source_text[:100000]}\nSOURCE_END"
        )
    prompt = (
        f"Create {count} flashcards. Title/topic: {title}. Subject: {subject}. "
        f"Difficulty: {difficulty}. Language code: {language}. Student grade/level: {grade or 'unspecified'}. Learning medium: {medium or language}. Keep every card safe and strictly appropriate to this grade.{source_instruction}"
    )
    raw = chat_completion(SYSTEM_PROMPT, prompt, temperature=0.25)
    return _parse_response(raw, count, {
        "title": title, "subject": subject, "language": language, "difficulty": difficulty,
        "source_type": source_type, "source_name": source_name,
    })


def generate_flashcards(topic: str, count: int) -> list[dict]:
    result = generate_flashcard_set(
        title=topic, subject="Other", count=count, difficulty="medium", language="en"
    )
    return [{"question": card.question, "answer": card.answer} for card in result.cards]
