from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.notification import Notification

def list_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    unread = query.filter(Notification.is_read.is_(False)).count()
    return items, total, unread

def unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).count()

def get_owned(db: Session, user_id: int, notification_id: int):
    return db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()

def mark_read(db: Session, item: Notification):
    if not item.is_read:
        item.is_read = True
        item.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item

def mark_all_read(db: Session, user_id: int) -> int:
    updated = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).update(
        {Notification.is_read: True, Notification.read_at: datetime.now(timezone.utc)}, synchronize_session=False)
    db.commit()
    return updated
