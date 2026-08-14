"""Local/S3 object storage without exposing bucket credentials or public ACLs."""
import os
import re
import uuid
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import boto3
from botocore.config import Config
from fastapi import HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.config.settings import settings

_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


def using_s3() -> bool:
    return settings.STORAGE_BACKEND.lower() == "s3"


def _key(category: str, extension: str) -> str:
    category = category.strip("/")
    candidate = f"{category}/{uuid.uuid4().hex}{extension.lower()}"
    path = PurePosixPath(candidate)
    if not _SAFE_KEY.fullmatch(candidate) or path.is_absolute() or ".." in path.parts or "\\" in candidate:
        raise HTTPException(400, "Invalid storage path")
    return candidate


def _client():
    return boto3.client(
        "s3", endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def object_key(reference: str) -> str | None:
    prefix = "s3://" if reference.startswith("s3://") else "/files/" if reference.startswith("/files/") else None
    if not prefix:
        return None
    key = reference[len(prefix):]
    path = PurePosixPath(key)
    if not key or not _SAFE_KEY.fullmatch(key) or path.is_absolute() or ".." in path.parts or "\\" in key:
        raise HTTPException(400, "Invalid storage path")
    return key


def store_bytes(data: bytes, category: str, extension: str, content_type: str,
                original_filename: str, *, private: bool = False, local_root: str | None = None) -> str:
    key = _key(category, extension)
    safe_name = Path(original_filename).name[:255] or f"file{extension}"
    if using_s3():
        _client().put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME, Key=key, Body=data,
            ContentType=content_type or "application/octet-stream",
            ContentDisposition=f"inline; filename*=UTF-8''{quote(safe_name)}",
            Metadata={"original-filename": quote(safe_name)},
        )
        return f"s3://{key}" if private else f"/files/{key}"
    root = Path(local_root or settings.UPLOAD_DIR)
    relative = Path(key).relative_to(category) if local_root else Path(key)
    target = (root / relative).resolve()
    root_resolved = root.resolve()
    if root_resolved != target.parent and root_resolved not in target.parents:
        raise HTTPException(400, "Invalid storage path")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(data)
    return str(target) if private else f"/uploads/{key}"


def presigned_url(reference: str, filename: str | None = None, content_type: str | None = None) -> str:
    key = object_key(reference)
    if not key:
        raise HTTPException(404, "Stored file not found")
    params = {"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f"inline; filename*=UTF-8''{quote(Path(filename).name)}"
    if content_type:
        params["ResponseContentType"] = content_type
    return _client().generate_presigned_url("get_object", Params=params,
        ExpiresIn=settings.PRIVATE_URL_EXPIRE_SECONDS)


def file_response(reference: str, *, filename: str | None = None, media_type: str | None = None,
                  local_root: str | None = None):
    if object_key(reference):
        return RedirectResponse(presigned_url(reference, filename, media_type), status_code=307)
    if reference.startswith("/uploads/"):
        root = Path(settings.UPLOAD_DIR).resolve()
        path = (root / reference.removeprefix("/uploads/")).resolve()
    else:
        root = Path(local_root).resolve() if local_root else Path(settings.UPLOAD_DIR).resolve()
        path = Path(reference).resolve()
    if (root != path and root not in path.parents) or not path.is_file():
        raise HTTPException(404, "Stored file not found")
    return FileResponse(path, filename=filename, media_type=media_type)


def read_bytes(reference: str, *, local_root: str | None = None) -> bytes:
    key = object_key(reference)
    if key:
        return _client().get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=key)["Body"].read()
    response = file_response(reference, local_root=local_root)
    return Path(response.path).read_bytes()


def delete_file(reference: str | None, *, local_root: str | None = None) -> None:
    if not reference:
        return
    key = object_key(reference)
    if key:
        _client().delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=key)
        return
    try:
        response = file_response(reference, local_root=local_root)
    except HTTPException as exc:
        if exc.status_code == 404:
            return
        raise
    Path(response.path).unlink(missing_ok=True)
