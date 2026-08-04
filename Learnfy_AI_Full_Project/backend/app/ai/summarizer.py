"""
AI Note Summarizer — condenses long notes / PDFs (already extracted to text)
into short, exam-friendly summaries.
"""
from app.services.ai_service import chat_completion

LENGTH_INSTRUCTIONS = {
    "short": "in 3-4 concise bullet points",
    "medium": "in a short paragraph of about 100-150 words, plus 3 key bullet points",
    "long": "in a detailed paragraph of about 250-350 words, plus 5-6 key bullet points",
}


def summarize_text(text: str, length: str = "medium") -> str:
    instruction = LENGTH_INSTRUCTIONS.get(length, LENGTH_INSTRUCTIONS["medium"])
    system_prompt = (
        "You are an expert study-notes summarizer for students. Summarize the given notes "
        f"{instruction}. Focus on the most important concepts, definitions, and facts. "
        "Do not add information that isn't in the original text."
    )
    return chat_completion(system_prompt, text, temperature=0.3)
