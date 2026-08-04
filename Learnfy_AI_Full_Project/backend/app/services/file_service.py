"""Validated local upload handling."""
import os
import uuid
from typing import Optional, Set
from fastapi import UploadFile, HTTPException
from app.config.settings import settings

DEFAULT_ALLOWED = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".ppt", ".pptx"}


def save_upload_file(file: UploadFile, category: str = "notes", allowed_extensions: Optional[Set[str]] = None) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required")
    ext = os.path.splitext(file.filename)[1].lower()
    allowed = allowed_extensions or DEFAULT_ALLOWED
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type '{ext or 'unknown'}' is not allowed")
    folder = os.path.join(settings.UPLOAD_DIR, category)
    os.makedirs(folder, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(folder, unique_name)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = 0
    try:
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
                buffer.write(chunk)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    finally:
        file.file.close()
    return f"/uploads/{category}/{unique_name}"
