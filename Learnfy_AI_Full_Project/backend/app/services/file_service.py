"""Validated local upload handling."""
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Set
from fastapi import UploadFile, HTTPException
from app.config.settings import settings
from app.services.storage_service import store_bytes

DEFAULT_ALLOWED = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".ppt", ".pptx"}
logger = logging.getLogger("learnfy.uploads")
MIME_BY_EXT = {
    ".pdf":{"application/pdf"}, ".docx":{"application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/zip","application/octet-stream"},
    ".pptx":{"application/vnd.openxmlformats-officedocument.presentationml.presentation","application/zip","application/octet-stream"},
    ".txt":{"text/plain"}, ".png":{"image/png"}, ".jpg":{"image/jpeg"}, ".jpeg":{"image/jpeg"},
    ".webp":{"image/webp"}, ".doc":{"application/msword","application/octet-stream"},
    ".ppt":{"application/vnd.ms-powerpoint","application/octet-stream"},
}

def _validate_signature(ext: str, data: bytes) -> None:
    signatures = {".pdf":(b"%PDF-",), ".png":(b"\x89PNG\r\n\x1a\n",),
                  ".jpg":(b"\xff\xd8\xff",), ".jpeg":(b"\xff\xd8\xff",),
                  ".webp":(b"RIFF",), ".doc":(b"\xd0\xcf\x11\xe0",), ".ppt":(b"\xd0\xcf\x11\xe0",)}
    if ext in signatures and not data.startswith(signatures[ext]):
        raise HTTPException(400, "File content does not match its extension")
    if ext == ".webp" and data[8:12] != b"WEBP":
        raise HTTPException(400, "File content does not match its extension")
    if ext in {".docx", ".pptx"}:
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                names = set(archive.namelist())
                marker = "word/document.xml" if ext == ".docx" else "ppt/presentation.xml"
                if "[Content_Types].xml" not in names or marker not in names:
                    raise HTTPException(400, "Invalid Office document container")
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, "Invalid Office document container") from exc


def save_upload_file(file: UploadFile, category: str = "notes", allowed_extensions: Optional[Set[str]] = None,
                     *, max_mb: int | None = None, private: bool = False, local_root: str | None = None) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required")
    safe_original = Path(file.filename).name
    ext = Path(safe_original).suffix.lower()
    allowed = allowed_extensions or DEFAULT_ALLOWED
    if ext not in allowed:
        logger.warning("upload_rejected category=%s reason=extension", category)
        raise HTTPException(status_code=400, detail=f"File type '{ext or 'unknown'}' is not allowed")
    declared_mime = (file.content_type or "application/octet-stream").lower()
    if ext in MIME_BY_EXT and declared_mime not in MIME_BY_EXT[ext]:
        logger.warning("upload_rejected category=%s reason=mime_mismatch", category)
        raise HTTPException(400, "File MIME type does not match its extension")
    max_size_mb = max_mb or settings.MAX_UPLOAD_SIZE_MB
    max_bytes = max_size_mb * 1024 * 1024
    size = 0
    try:
        chunks = []
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                logger.warning("upload_rejected category=%s reason=size", category)
                raise HTTPException(status_code=413, detail=f"File exceeds {max_size_mb}MB limit")
            chunks.append(chunk)
        data = b"".join(chunks)
        _validate_signature(ext, data)
        return store_bytes(data, category, ext, declared_mime, safe_original,
                           private=private, local_root=local_root)
    finally:
        file.file.close()
