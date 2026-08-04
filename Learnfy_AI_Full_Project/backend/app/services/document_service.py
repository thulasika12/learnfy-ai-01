"""Extract text from uploaded TXT, PDF and DOCX study documents."""
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from app.config.settings import settings

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def extract_text_from_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A document is required")

    extension = Path(file.filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Upload a TXT, Markdown, PDF, or DOCX file")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    file.file.close()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    try:
        if extension in {".txt", ".md"}:
            text = data.decode("utf-8", errors="replace")
        elif extension == ".pdf":
            reader = PdfReader(BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            document = Document(BytesIO(data))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded document could not be read") from exc

    text = text.strip()
    if len(text) < 10:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found. Scanned PDFs need OCR before summarizing.",
        )
    return text


def extract_text_from_path(path: str) -> str:
    """Extract a previously stored document using the same validated parser."""
    file_path = Path(path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="The note document is unavailable")
    with file_path.open("rb") as handle:
        upload = UploadFile(filename=file_path.name, file=BytesIO(handle.read()))
    return extract_text_from_upload(upload)
