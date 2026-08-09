"""
Notes routes: upload, list (with search/filter), get one, delete, like, bookmark.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.models.note import Note, Like, Bookmark
from app.models.user import User, UserRole
from app.schemas.note_schema import NoteOut, NoteUpdate
from app.services.file_service import save_upload_file
from app.utils.dependencies import get_current_user, get_optional_current_user

router = APIRouter(prefix="/notes", tags=["Notes"])


def _serialize_note(note: Note, current_user: Optional[User], db: Session) -> NoteOut:
    likes_count = db.query(Like).filter(Like.note_id == note.id).count()
    comments_count = len(note.comments)
    is_liked = False
    is_bookmarked = False
    if current_user:
        is_liked = (
            db.query(Like).filter(Like.note_id == note.id, Like.user_id == current_user.id).first()
            is not None
        )
        is_bookmarked = (
            db.query(Bookmark)
            .filter(Bookmark.note_id == note.id, Bookmark.user_id == current_user.id)
            .first()
            is not None
        )

    data = NoteOut.model_validate(note)
    data.likes_count = likes_count
    data.comments_count = comments_count
    data.is_liked = is_liked
    data.is_bookmarked = is_bookmarked
    return data


@router.post("/", response_model=NoteOut, status_code=201)
def upload_note(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    subject: str = Form(...),
    grade: Optional[str] = Form(None),
    stream: Optional[str] = Form(None),
    medium: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new note, optionally attaching a file (PDF/doc/image)."""
    file_url = save_upload_file(file, category="notes") if file else None

    note = Note(
        title=title,
        description=description,
        subject=subject,
        grade=grade,
        stream=stream,
        medium=medium,
        file_url=file_url,
        user_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note, current_user, db)


@router.get("/", response_model=list[NoteOut])
def list_notes(
    search: Optional[str] = Query(None, description="Search by title or description"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    medium: Optional[str] = Query(None, description="Filter by medium"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """List all notes with optional search and subject filter (public endpoint)."""
    query = db.query(Note).options(joinedload(Note.author)).filter(Note.is_hidden.is_(False))

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            (Note.title.ilike(like_pattern)) | (Note.description.ilike(like_pattern))
        )
    if subject:
        query = query.filter(Note.subject == subject)
    if grade:
        query = query.filter(Note.grade == grade)
    if medium:
        query = query.filter(Note.medium == medium)

    notes = query.order_by(Note.created_at.desc()).offset(skip).limit(limit).all()
    return [_serialize_note(n, current_user, db) for n in notes]


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    note = db.query(Note).options(joinedload(Note.author)).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.is_hidden and not (current_user and (current_user.id == note.user_id or current_user.role == UserRole.admin)):
        raise HTTPException(status_code=404, detail="Note not found")
    return _serialize_note(note, current_user, db)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).options(joinedload(Note.author)).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="You can only edit your own notes")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return _serialize_note(note, current_user, db)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="You can only delete your own notes")

    db.delete(note)
    db.commit()
    return None


@router.post("/{note_id}/like", status_code=200)
def toggle_like(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    existing = db.query(Like).filter(Like.note_id == note_id, Like.user_id == current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"liked": False}

    db.add(Like(note_id=note_id, user_id=current_user.id))
    db.commit()
    return {"liked": True}


@router.post("/{note_id}/bookmark", status_code=200)
def toggle_bookmark(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    existing = (
        db.query(Bookmark).filter(Bookmark.note_id == note_id, Bookmark.user_id == current_user.id).first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"bookmarked": False}

    db.add(Bookmark(note_id=note_id, user_id=current_user.id))
    db.commit()
    return {"bookmarked": True}
