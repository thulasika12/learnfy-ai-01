from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.chat import AIChat
from app.models.group import GroupMember
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.dashboard_schema import DashboardStats
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return DashboardStats(
        uploaded_notes=db.query(func.count(Note.id)).filter(Note.user_id == current_user.id).scalar() or 0,
        ai_doubts=db.query(func.count(AIChat.id)).filter(AIChat.user_id == current_user.id).scalar() or 0,
        quizzes_generated=db.query(func.count(distinct(Quiz.quiz_batch_id))).filter(
            Quiz.user_id == current_user.id, Quiz.quiz_batch_id.is_not(None)
        ).scalar() or 0,
        study_groups=db.query(func.count(GroupMember.id)).filter(GroupMember.user_id == current_user.id).scalar() or 0,
    )
