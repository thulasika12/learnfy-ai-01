from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    title: str
    message: str
    link: str | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread_count: int
    total: int

class UnreadCount(BaseModel):
    unread_count: int
