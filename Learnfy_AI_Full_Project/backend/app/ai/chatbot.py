"""
AI Doubt Solver — answers academic questions from students in a clear,
step-by-step, teacher-like tone.
"""
from app.services.ai_service import chat_completion

SYSTEM_PROMPT = (
    "You are 'Learnfy AI Tutor', a friendly and knowledgeable academic assistant. "
    "Explain concepts clearly and step-by-step, use simple language, give examples where useful, "
    "and keep answers focused on helping the student truly understand the topic rather than just "
    "giving a final answer."
)


def solve_doubt(question: str) -> str:
    return chat_completion(SYSTEM_PROMPT, question, temperature=0.6)
