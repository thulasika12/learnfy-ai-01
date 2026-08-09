"""
Educational resource routes for teachers (upload/manage study materials).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.services.file_service import save_upload_file
from app.utils.dependencies import get_current_user, require_teacher

router = APIRouter(prefix="/resources", tags=["Teacher Resources"])


@router.post("/", status_code=201)
def upload_resource(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    subject: str = Form(...),
    grade: Optional[str] = Form(None),
    stream: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Teachers (and admins) can upload educational resources / study materials."""
    file_url = save_upload_file(file, category="resources") if file else None
    resource = Resource(
        title=title,
        description=description,
        subject=subject,
        grade=grade,
        stream=stream,
        medium=medium,
        file_url=file_url,
        teacher_id=current_user.id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("/")
def list_resources(grade: Optional[str] = None, subject: Optional[str] = None, medium: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Resource).filter(Resource.is_hidden.is_(False))
    if grade: query = query.filter(Resource.grade == grade)
    if subject: query = query.filter(Resource.subject == subject)
    if medium: query = query.filter(Resource.medium == medium)
    return query.order_by(Resource.created_at.desc()).all()


@router.delete("/{resource_id}", status_code=204)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.teacher_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="You can only delete your own resources")

    db.delete(resource)
    db.commit()
    return None
