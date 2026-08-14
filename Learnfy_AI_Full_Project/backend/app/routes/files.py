from fastapi import APIRouter
from app.services.storage_service import file_response

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("/{object_path:path}")
def view_file(object_path: str):
    return file_response(f"/files/{object_path}")
