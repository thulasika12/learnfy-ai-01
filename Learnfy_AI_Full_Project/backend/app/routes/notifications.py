from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification_schema import NotificationList, NotificationOut, UnreadCount
from app.services import notification_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=NotificationList)
def get_notifications(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items, total, unread = notification_service.list_for_user(db, current_user.id, skip, limit)
    return {"items": items, "total": total, "unread_count": unread}

@router.get("/unread-count", response_model=UnreadCount)
def get_unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"unread_count": notification_service.unread_count(db, current_user.id)}

@router.patch("/read-all", response_model=UnreadCount)
def read_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification_service.mark_all_read(db, current_user.id)
    return {"unread_count": 0}

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = notification_service.get_owned(db, current_user.id, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification_service.mark_read(db, item)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = notification_service.get_owned(db, current_user.id, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/dev/sample", response_model=NotificationList, status_code=201)
def create_development_samples(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if settings.ENVIRONMENT.lower() != "development":
        raise HTTPException(status_code=404, detail="Not found")
    if db.query(Notification).filter(Notification.user_id == current_user.id).count() == 0:
        samples = [
            ("group", "New study group invitation", "You have been invited to join a study group.", "/groups"),
            ("reminder", "Flashcard revision reminder", "Your daily flashcard revision is ready.", "/ai/flashcards"),
            ("quiz", "Quiz result available", "Your latest quiz result is ready to review.", "/progress"),
            ("reply", "New reply to a doubt", "Someone replied to your recent discussion.", "/groups"),
        ]
        db.add_all([Notification(user_id=current_user.id, type=t, title=a, message=m, link=l) for t, a, m, l in samples])
        db.commit()
    items, total, unread = notification_service.list_for_user(db, current_user.id)
    return {"items": items, "total": total, "unread_count": unread}
