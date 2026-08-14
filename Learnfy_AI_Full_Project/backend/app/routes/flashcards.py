"""Complete private AI flashcard API with study, export, sharing, and reminders."""
import os
import secrets
from io import BytesIO
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.ai.flashcard_generator import generate_flashcard_set
from app.config.database import get_db
from app.config.settings import settings
from app.models.flashcard import (
    Flashcard, FlashcardReminder, FlashcardSessionAnswer, FlashcardSet, FlashcardStudySession,
)
from app.models.note import Note
from app.models.user import User
from app.schemas.flashcard_schema import (
    DashboardStats, GenerateFromNoteRequest, GenerateFromTextRequest, GenerateRequest, GeneratedSet,
    ReminderOut, ReminderUpdate, SetCreate, SetOut, SetUpdate, ShareOut, ShareRequest,
    StudySessionCreate, StudySessionOut,
)
from app.services.document_service import extract_text_from_path, extract_text_from_upload
from app.services.file_service import save_upload_file
from app.services.storage_service import delete_file, read_bytes
from app.services.flashcard_export_service import build_csv, build_pdf, safe_export_name
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)


def owned_set(db: Session, set_id: int, user_id: int) -> FlashcardSet:
    item = (
        db.query(FlashcardSet).options(selectinload(FlashcardSet.cards))
        .filter(FlashcardSet.id == set_id, FlashcardSet.user_id == user_id).first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    return item


def set_output(item: FlashcardSet) -> SetOut:
    best = max((session.score_percentage for session in item.study_sessions), default=None)
    data = SetOut.model_validate(item)
    data.best_score = best
    return data


@router.post("/generate", response_model=GeneratedSet)
def generate(payload: GenerateRequest, _: User = Depends(get_current_user)):
    return generate_flashcard_set(
        title=payload.topic, subject=payload.subject, count=payload.count,
        difficulty=payload.difficulty, language=payload.language, grade=payload.grade, medium=payload.medium,
    )


@router.post("/generate-from-text", response_model=GeneratedSet)
def generate_from_text(payload: GenerateFromTextRequest, _: User = Depends(get_current_user)):
    return generate_flashcard_set(
        title=payload.title, subject=payload.subject, count=payload.count,
        difficulty=payload.difficulty, language=payload.language, grade=payload.grade, medium=payload.medium,
        source_type="text", source_name=payload.title, source_text=payload.text,
    )


@router.post("/generate-from-pdf", response_model=GeneratedSet)
def generate_from_pdf(
    file: UploadFile = File(...), title: str = Form(...), subject: str = Form("Other"),
    count: int = Form(10, ge=1, le=30), difficulty: str = Form("medium"),
    language: str = Form("en"), grade: str = Form(...), medium: str = Form(...), _: User = Depends(get_current_user),
):
    if Path(file.filename or "").suffix.lower() != ".pdf" or file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a valid PDF file")
    if difficulty not in {"easy", "medium", "hard"} or language not in {"en", "ta", "si"}:
        raise HTTPException(status_code=422, detail="Invalid difficulty or language")
    text = extract_text_from_upload(file)
    return generate_flashcard_set(
        title=title, subject=subject, count=count, difficulty=difficulty, language=language,
        source_type="pdf", source_name=Path(file.filename).name[:255], source_text=text, grade=grade, medium=medium,
    )


@router.post("/generate-from-document", response_model=GeneratedSet)
def generate_from_document(
    file: UploadFile = File(...), title: str = Form(...), subject: str = Form("Other"),
    count: int = Form(10, ge=1, le=30), difficulty: str = Form("medium"),
    language: str = Form("en"), grade: str = Form(...), medium: str = Form(...), _: User = Depends(get_current_user),
):
    text = extract_text_from_upload(file)
    return generate_flashcard_set(
        title=title, subject=subject, count=count, difficulty=difficulty, language=language,
        source_type="document", source_name=Path(file.filename or "document").name[:255], source_text=text, grade=grade, medium=medium,
    )


@router.post("/generate-from-note", response_model=GeneratedSet)
def generate_from_note(
    payload: GenerateFromNoteRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == payload.note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    parts = [note.title, note.description or ""]
    if note.file_url:
        if note.file_url.startswith(("s3://", "/files/")):
            upload = UploadFile(file=BytesIO(read_bytes(note.file_url)), filename=Path(note.file_url).name)
            parts.append(extract_text_from_upload(upload))
        else:
            relative = note.file_url.removeprefix("/uploads/")
            parts.append(extract_text_from_path(os.path.join(settings.UPLOAD_DIR, relative)))
    text = "\n".join(part for part in parts if part).strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="This note does not contain enough readable text")
    return generate_flashcard_set(
        title=note.title, subject=note.subject, count=payload.count,
        difficulty=payload.difficulty, language=payload.language,
        source_type="note", source_name=note.title, source_text=text, grade=note.grade, medium=note.medium,
    )


@router.post("/sets", response_model=SetOut, status_code=201)
def create_set(payload: SetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = FlashcardSet(user_id=user.id, **payload.model_dump(exclude={"cards"}))
    for index, card in enumerate(payload.cards):
        item.cards.append(Flashcard(**card.model_dump(), sort_order=index))
    db.add(item); db.commit(); db.refresh(item)
    return set_output(item)


@router.get("/sets", response_model=list[SetOut])
def list_sets(
    search: str | None = Query(default=None, max_length=100), subject: str | None = Query(default=None, max_length=100),
    favourites: bool = False, sort: str = Query(default="newest", pattern="^(newest|oldest|title|highest_score)$"),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(FlashcardSet).options(selectinload(FlashcardSet.cards), selectinload(FlashcardSet.study_sessions)).filter(FlashcardSet.user_id == user.id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(FlashcardSet.title.ilike(term), FlashcardSet.subject.ilike(term)))
    if subject:
        query = query.filter(FlashcardSet.subject == subject)
    if favourites:
        query = query.filter(FlashcardSet.is_favourite.is_(True))
    if sort == "oldest": query = query.order_by(FlashcardSet.created_at.asc())
    elif sort == "title": query = query.order_by(FlashcardSet.title.asc())
    else: query = query.order_by(FlashcardSet.created_at.desc())
    results = [set_output(item) for item in query.all()]
    if sort == "highest_score": results.sort(key=lambda item: item.best_score or -1, reverse=True)
    return results


@router.get("/sets/{set_id}", response_model=SetOut)
def get_set(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return set_output(owned_set(db, set_id, user.id))


@router.put("/sets/{set_id}", response_model=SetOut)
def update_set(payload: SetUpdate, set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_set(db, set_id, user.id)
    changes = payload.model_dump(exclude_unset=True, exclude={"cards"})
    for key, value in changes.items(): setattr(item, key, value)
    if payload.cards is not None:
        item.cards.clear(); db.flush()
        for index, card in enumerate(payload.cards): item.cards.append(Flashcard(**card.model_dump(), sort_order=index))
    db.commit(); db.refresh(item)
    return set_output(item)


@router.delete("/sets/{set_id}", status_code=204)
def delete_set(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(owned_set(db, set_id, user.id)); db.commit()


@router.patch("/sets/{set_id}/favourite", response_model=SetOut)
def favourite_set(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_set(db, set_id, user.id); item.is_favourite = not item.is_favourite
    db.commit(); db.refresh(item); return set_output(item)


@router.patch("/cards/{card_id}/favourite")
def favourite_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Flashcard).join(FlashcardSet).filter(Flashcard.id == card_id, FlashcardSet.user_id == user.id).first()
    if not card: raise HTTPException(status_code=404, detail="Flashcard not found")
    card.is_favourite = not card.is_favourite; db.commit()
    return {"id": card.id, "is_favourite": card.is_favourite}


@router.post("/cards/{card_id}/image")
def upload_card_image(card_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Flashcard).join(FlashcardSet).filter(Flashcard.id == card_id, FlashcardSet.user_id == user.id).first()
    if not card: raise HTTPException(status_code=404, detail="Flashcard not found")
    previous = card.image_url
    card.image_url = save_upload_file(file, category="flashcards", allowed_extensions={".jpg", ".jpeg", ".png", ".webp"})
    db.commit(); delete_file(previous); return {"image_url": card.image_url}


@router.post("/sets/{set_id}/study-sessions", response_model=StudySessionOut, status_code=201)
def save_session(payload: StudySessionCreate, set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_set(db, set_id, user.id); valid_ids = {card.id for card in item.cards}
    submitted = {answer.card_id for answer in payload.answers}
    if submitted != valid_ids: raise HTTPException(status_code=400, detail="Submit one result for every card in this set")
    correct = sum(answer.status == "known" for answer in payload.answers); total = len(payload.answers)
    session = FlashcardStudySession(user_id=user.id, set_id=set_id, correct_count=correct, incorrect_count=total-correct, total_cards=total, score_percentage=round(correct / total * 100, 2), duration_seconds=payload.duration_seconds)
    for answer in payload.answers: session.answers.append(FlashcardSessionAnswer(card_id=answer.card_id, status=answer.status))
    db.add(session); db.commit(); db.refresh(session); return session


@router.get("/sets/{set_id}/study-sessions", response_model=list[StudySessionOut])
def sessions(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_set(db, set_id, user.id)
    return db.query(FlashcardStudySession).filter_by(set_id=set_id, user_id=user.id).order_by(FlashcardStudySession.completed_at.desc()).all()


@router.post("/sets/{set_id}/share", response_model=ShareOut)
def share(payload: ShareRequest, set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_set(db, set_id, user.id); item.is_public = True
    item.share_token = item.share_token or secrets.token_urlsafe(32)
    item.share_expires_at = utcnow() + timedelta(days=payload.expires_in_days) if payload.expires_in_days else None
    db.commit(); return ShareOut(share_token=item.share_token, share_url=f"{settings.FRONTEND_URL.rstrip('/')}/flashcards/shared/{item.share_token}", expires_at=item.share_expires_at)


@router.delete("/sets/{set_id}/share", status_code=204)
def unshare(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_set(db, set_id, user.id); item.is_public = False; item.share_token = None; item.share_expires_at = None; db.commit()


@router.get("/shared/{share_token}", response_model=SetOut)
def shared_set(share_token: str, db: Session = Depends(get_db)):
    item = db.query(FlashcardSet).options(selectinload(FlashcardSet.cards)).filter_by(share_token=share_token, is_public=True).first()
    if not item or (item.share_expires_at and as_utc(item.share_expires_at) <= utcnow()):
        raise HTTPException(status_code=404, detail="Shared flashcard set not found or link expired")
    return set_output(item)


def export_set(set_id: int, kind: str, db: Session, user: User) -> Response:
    item = owned_set(db, set_id, user.id)
    content = build_pdf(item) if kind == "pdf" else build_csv(item)
    media = "application/pdf" if kind == "pdf" else "text/csv; charset=utf-8"
    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{safe_export_name(item.title, kind)}"'})


@router.get("/sets/{set_id}/export/pdf")
def export_pdf(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return export_set(set_id, "pdf", db, user)


@router.get("/sets/{set_id}/export/csv")
def export_csv(set_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return export_set(set_id, "csv", db, user)


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_sets = db.query(FlashcardSet).filter_by(user_id=user.id).count()
    aggregate = db.query(func.coalesce(func.sum(FlashcardStudySession.total_cards), 0), func.coalesce(func.avg(FlashcardStudySession.score_percentage), 0)).filter_by(user_id=user.id).one()
    days = [row[0].date() if isinstance(row[0], datetime) else row[0] for row in db.query(FlashcardStudySession.completed_at).filter_by(user_id=user.id).distinct().all()]
    streak = 0; cursor = date.today()
    if cursor not in days and cursor - timedelta(days=1) in days: cursor -= timedelta(days=1)
    while cursor in days: streak += 1; cursor -= timedelta(days=1)
    return DashboardStats(total_sets=total_sets, total_cards_studied=int(aggregate[0]), average_score=round(float(aggregate[1]), 2), revision_streak=streak)


@router.get("/reminders", response_model=ReminderOut | None)
def get_reminder(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FlashcardReminder).filter_by(user_id=user.id).first()


@router.put("/reminders", response_model=ReminderOut)
def update_reminder(payload: ReminderUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reminder = db.query(FlashcardReminder).filter_by(user_id=user.id).first()
    if not reminder: reminder = FlashcardReminder(user_id=user.id, reminder_time=payload.reminder_time, timezone=payload.timezone); db.add(reminder)
    reminder.is_enabled = payload.is_enabled; reminder.reminder_time = payload.reminder_time; reminder.timezone = payload.timezone
    db.commit(); db.refresh(reminder); return reminder
