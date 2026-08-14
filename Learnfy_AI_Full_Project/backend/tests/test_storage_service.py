from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

from app.config.settings import settings
from app.services import storage_service
from app.services.file_service import save_upload_file


class FakeS3:
    def __init__(self):
        self.put = None
        self.deleted = None
        self.presigned = None

    def put_object(self, **kwargs): self.put = kwargs
    def delete_object(self, **kwargs): self.deleted = kwargs
    def generate_presigned_url(self, operation, **kwargs):
        self.presigned = (operation, kwargs)
        return "https://bucket.invalid/signed"


def upload(name, content, content_type):
    return UploadFile(file=BytesIO(content), filename=name, headers={"content-type": content_type})


def test_s3_upload_uses_private_object_and_safe_unique_key(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "private-bucket")
    monkeypatch.setattr(storage_service, "_client", lambda: fake)
    reference = save_upload_file(upload("../lesson.pdf", b"%PDF-1.4\n", "application/pdf"), "notes")
    assert reference.startswith("/files/notes/") and reference.endswith(".pdf")
    assert fake.put["Bucket"] == "private-bucket"
    assert fake.put["ContentType"] == "application/pdf"
    assert "ACL" not in fake.put
    assert ".." not in fake.put["Key"]


def test_presigned_download_and_delete(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(settings, "AWS_S3_BUCKET_NAME", "private-bucket")
    monkeypatch.setattr(settings, "PRIVATE_URL_EXPIRE_SECONDS", 321)
    monkeypatch.setattr(storage_service, "_client", lambda: fake)
    assert storage_service.presigned_url("s3://private/a.pdf", "a.pdf", "application/pdf").endswith("/signed")
    assert fake.presigned[1]["ExpiresIn"] == 321
    storage_service.delete_file("/files/private/a.pdf")
    assert fake.deleted == {"Bucket": "private-bucket", "Key": "private/a.pdf"}


def test_invalid_content_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    with pytest.raises(HTTPException) as error:
        save_upload_file(upload("bad.pdf", b"not a pdf", "application/pdf"), "notes")
    assert error.value.status_code == 400


def test_local_storage_fallback_and_legacy_read(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    reference = save_upload_file(upload("photo.png", b"\x89PNG\r\n\x1a\nbody", "image/png"), "profile")
    assert reference.startswith("/uploads/profile/")
    assert storage_service.read_bytes(reference) == b"\x89PNG\r\n\x1a\nbody"
    storage_service.delete_file(reference)
    assert not (tmp_path / reference.removeprefix("/uploads/")).exists()


def test_storage_reference_rejects_traversal():
    with pytest.raises(HTTPException):
        storage_service.object_key("/files/../secret.pdf")
