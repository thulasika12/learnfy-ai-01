from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.config.database import get_db
from app.models.flashcard import FlashcardSet
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.resource import Resource
from app.models.subject import Subject, SubjectStream
from app.models.academic import GradeSubject
from app.models.user import User
from app.schemas.subject_schema import STREAMS, SubjectOut, SubjectWrite
from app.utils.dependencies import require_admin
from app.services.audit_service import add_admin_audit

router = APIRouter(tags=["Subjects"])

def serialize(item):
    data = SubjectOut.model_validate(item)
    data.streams = [link.stream for link in item.stream_links] or [item.stream]
    return data

def replace_streams(db, item, streams):
    item.stream_links.clear()
    for stream in list(dict.fromkeys(streams or [item.stream])):
        item.stream_links.append(SubjectStream(stream=stream))

@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(level: str | None = Query(None), stream: str | None = None, grade_id: int | None = None, medium: str | None = None, search: str | None = None,
                  db: Session = Depends(get_db)):
    query = db.query(Subject).options(joinedload(Subject.stream_links))
    if level: query = query.filter(Subject.level == level)
    query = query.filter(Subject.is_active.is_(True))
    if stream: query = query.join(SubjectStream).filter(SubjectStream.stream == stream)
    if grade_id:
        query = query.join(GradeSubject).filter(GradeSubject.grade_id == grade_id, GradeSubject.is_active.is_(True))
        if medium: query = query.filter(GradeSubject.medium.in_(["all", medium]))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Subject.subject_code.ilike(term), Subject.name_en.ilike(term), Subject.name_ta.ilike(term), Subject.name_si.ilike(term)))
    return [serialize(item) for item in query.order_by(Subject.sort_order, Subject.subject_code).all()]

@router.get("/admin/subjects", response_model=list[SubjectOut])
def list_admin_subjects(level: str = "AL", stream: str | None = None, search: str | None = None,
                        db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = db.query(Subject).options(joinedload(Subject.stream_links)).filter(Subject.level == level)
    if stream: query = query.join(SubjectStream).filter(SubjectStream.stream == stream)
    if search:
        term = f"%{search.strip()}%"; query = query.filter(or_(Subject.subject_code.ilike(term), Subject.name_en.ilike(term)))
    return [serialize(item) for item in query.order_by(Subject.sort_order, Subject.subject_code).all()]

@router.get("/subjects/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    item = db.query(Subject).options(joinedload(Subject.stream_links)).filter(Subject.id == subject_id, Subject.is_active.is_(True)).first()
    if not item: raise HTTPException(404, "Subject not found")
    return serialize(item)

@router.post("/admin/subjects", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectWrite, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(Subject).filter(Subject.level == payload.level, Subject.subject_code == payload.subject_code).first():
        raise HTTPException(409, "Subject code already exists for this level")
    if db.query(Subject).filter(Subject.level == payload.level, Subject.stream == payload.stream, Subject.name_en == payload.name_en).first():
        raise HTTPException(409, "This subject already exists for the selected level and stream")
    values = payload.model_dump(exclude={"streams"}); item = Subject(**values)
    replace_streams(db, item, payload.streams or [payload.stream]); db.add(item); db.flush()
    add_admin_audit(db, admin.id, "subject.create", "subject", item.id, item.subject_code)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409, "Subject code already exists for this level")
    db.refresh(item); return serialize(item)

@router.put("/admin/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectWrite, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item = db.query(Subject).options(joinedload(Subject.stream_links)).filter(Subject.id == subject_id).first()
    if not item: raise HTTPException(404, "Subject not found")
    duplicate = db.query(Subject).filter(Subject.level == payload.level, Subject.subject_code == payload.subject_code, Subject.id != subject_id).first()
    if duplicate: raise HTTPException(409, "Subject code already exists for this level")
    if db.query(Subject).filter(Subject.level == payload.level, Subject.stream == payload.stream, Subject.name_en == payload.name_en, Subject.id != subject_id).first(): raise HTTPException(409, "This subject already exists for the selected level and stream")
    for key, value in payload.model_dump(exclude={"streams"}).items(): setattr(item, key, value)
    replace_streams(db, item, payload.streams or [payload.stream]); add_admin_audit(db, admin.id, "subject.update", "subject", item.id, item.subject_code); db.commit(); db.refresh(item); return serialize(item)

@router.delete("/admin/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item = db.query(Subject).filter(Subject.id == subject_id).first()
    if not item: raise HTTPException(404, "Subject not found")
    used = any(db.query(model).filter(model.subject == item.name_en).first() for model in (Note, Resource, Quiz, FlashcardSet))
    if used:
        item.is_active = False; add_admin_audit(db, admin.id, "subject.deactivate", "subject", item.id, item.subject_code); db.commit()
    else:
        code = item.subject_code; db.delete(item); add_admin_audit(db, admin.id, "subject.delete", "subject", subject_id, code); db.commit()
    return Response(status_code=204)
