"""
Routes for retrieving a student's past AI chat history (separate from the
/ai/chat action route so the chat history can be paginated independently).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.chat import AIChat
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat History"])


@router.get("/history")
def get_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the current user's past AI doubt-solver conversations."""
    chats = (
        db.query(AIChat)
        .filter(AIChat.user_id == current_user.id)
        .order_by(AIChat.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {"id": c.id, "question": c.question, "answer": c.answer, "created_at": c.created_at}
        for c in chats
    ]
