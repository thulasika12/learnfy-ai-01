"""Student-safety validation for academic group communication."""
import re
from fastapi import HTTPException

CONTACT_BLOCKED_MESSAGE = "Phone numbers and personal contact details cannot be shared in Study Groups."
PHOTO_BLOCKED_MESSAGE = "Personal photos cannot be shared in Study Groups. Share an approved learning resource instead."

# Candidates must either be an explicit international number, or a Sri Lankan
# mobile beginning 07. Separators are accepted, while ordinary marks, years,
# lesson numbers and calculations are deliberately outside these shapes.
_PHONE_CANDIDATE = re.compile(r"(?<!\w)(?:\+|00)?[\d(][\d\s().-]{7,22}\d(?!\w)")

def contains_phone_number(value: str) -> bool:
    for match in _PHONE_CANDIDATE.finditer(value or ""):
        raw = match.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("00947") and len(digits) == 14:
            return True
        if raw.startswith("+") and 10 <= len(digits) <= 15:
            return True
        if digits.startswith("07") and len(digits) == 10:
            return True
        if raw.startswith("00") and 10 <= len(digits) <= 17:
            return True
    return False

def validate_group_text(value: str) -> str:
    clean = (value or "").strip()
    if contains_phone_number(clean):
        # Never include the rejected content in the exception or logs.
        raise HTTPException(status_code=422, detail=CONTACT_BLOCKED_MESSAGE)
    return clean
