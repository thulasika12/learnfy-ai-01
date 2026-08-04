"""Authenticated content reporting without automatic moderation actions."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.content_report import ContentReport, ReportStatus
from app.models.group import StudyGroup
from app.models.note import Note
from app.models.resource import Resource
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])
TARGETS = {"note": Note, "resource": Resource, "group": StudyGroup, "user": User}


class ReportRequest(BaseModel):
    target_type: str
    target_id: int
    reason: str = Field(min_length=3, max_length=1000)


@router.post("", status_code=201)
def create_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    model = TARGETS.get(payload.target_type)
    if not model:
        raise HTTPException(400, "Invalid report target")
    if not db.query(model).filter(model.id == payload.target_id).first():
        raise HTTPException(404, "Report target not found")
    duplicate = db.query(ContentReport).filter(
        ContentReport.reporter_id == user.id,
        ContentReport.target_type == payload.target_type,
        ContentReport.target_id == payload.target_id,
        ContentReport.status == ReportStatus.pending,
    ).first()
    if duplicate:
        raise HTTPException(409, "You already reported this item")
    item = ContentReport(reporter_id=user.id, target_type=payload.target_type, target_id=payload.target_id, reason=payload.reason.strip())
    if payload.target_type == "note":
        db.query(Note).filter(Note.id == payload.target_id).update({Note.is_reported: True})
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "status": item.status}
