"""
Comment routes for notes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.models.note import Comment, Note
from app.models.user import User
from app.schemas.note_schema import CommentCreate, CommentOut
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentOut, status_code=201)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(Note.id == payload.note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    comment = Comment(note_id=payload.note_id, user_id=current_user.id, comment=payload.comment)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{note_id}", response_model=list[CommentOut])
def get_comments(note_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.note_id == note_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return comments


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    db.delete(comment)
    db.commit()
    return None
