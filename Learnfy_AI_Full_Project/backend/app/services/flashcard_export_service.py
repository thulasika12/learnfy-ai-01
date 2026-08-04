"""CSV and Unicode-capable PDF exports for saved flashcard sets."""
import csv
import io
import re
from pathlib import Path

from fastapi import HTTPException
from app.config.settings import settings


def safe_export_name(title: str, extension: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", title).strip("-")[:80] or "flashcards"
    return f"{stem}.{extension}"


def build_csv(flashcard_set) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["number", "question", "answer", "subject", "difficulty", "language"])
    for index, card in enumerate(flashcard_set.cards, 1):
        writer.writerow([
            index, card.question, card.answer, flashcard_set.subject,
            flashcard_set.difficulty, flashcard_set.language,
        ])
    return stream.getvalue().encode("utf-8-sig")


def _unicode_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        settings.PDF_UNICODE_FONT_PATH,
        r"C:\Windows\Fonts\Nirmala.ttc",
        r"C:\Windows\Fonts\Nirmala.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            pdfmetrics.registerFont(TTFont("LearnfyUnicode", candidate))
            return "LearnfyUnicode"
    raise HTTPException(
        status_code=503,
        detail="PDF Unicode font is unavailable. Configure PDF_UNICODE_FONT_PATH with a Tamil/Sinhala capable TTF font.",
    )


def build_pdf(flashcard_set) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape

    font = _unicode_font()
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("UnicodeTitle", parent=styles["Title"], fontName=font, fontSize=18, leading=24)
    body_style = ParagraphStyle("UnicodeBody", parent=styles["BodyText"], fontName=font, fontSize=10, leading=15, spaceAfter=5)
    story = [
        Paragraph(escape(flashcard_set.title), title_style),
        Paragraph(escape(f"Subject: {flashcard_set.subject} | Language: {flashcard_set.language} | Difficulty: {flashcard_set.difficulty}"), body_style),
        Spacer(1, 8),
    ]
    for index, card in enumerate(flashcard_set.cards, 1):
        story.extend([
            Paragraph(escape(f"{index}. {card.question}"), body_style),
            Paragraph(escape(f"Answer: {card.answer}"), body_style),
            Spacer(1, 7),
        ])
    document.build(story)
    return output.getvalue()
