import io
import zipfile
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi import HTTPException, UploadFile
from app.services.file_service import save_upload_file

def upload(name, content, mime):
    return UploadFile(filename=name, file=io.BytesIO(content), headers={"content-type": mime})

def test_pdf_magic_and_random_storage_name(tmp_path):
    with patch("app.services.file_service.settings.UPLOAD_DIR", str(tmp_path)):
        url = save_upload_file(upload("../../lesson.pdf", b"%PDF-1.7\n%%EOF", "application/pdf"))
    assert "lesson.pdf" not in url
    assert Path(tmp_path, url.removeprefix("/uploads/")).is_file()

def test_mime_mismatch_rejected(tmp_path):
    with patch("app.services.file_service.settings.UPLOAD_DIR", str(tmp_path)):
        with pytest.raises(HTTPException) as error:
            save_upload_file(upload("lesson.pdf", b"MZ executable", "application/octet-stream"))
    assert error.value.status_code == 400

def test_valid_docx_container(tmp_path):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    with patch("app.services.file_service.settings.UPLOAD_DIR", str(tmp_path)):
        url = save_upload_file(upload("notes.docx", data.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    assert url.endswith(".docx")

def test_oversized_upload_removes_partial_file(tmp_path):
    with patch("app.services.file_service.settings.UPLOAD_DIR", str(tmp_path)), patch("app.services.file_service.settings.MAX_UPLOAD_SIZE_MB", 0):
        with pytest.raises(HTTPException) as error:
            save_upload_file(upload("lesson.pdf", b"%PDF-", "application/pdf"))
    assert error.value.status_code == 413
    assert not list(tmp_path.rglob("*.pdf"))
