"""
Pydantic schemas for Notes, Comments, Likes, Bookmarks and Study Groups.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user_schema import UserOut


class NoteCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    subject: str
    grade: Optional[str] = None
    stream: Optional[str] = None
    medium: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
    subject: Optional[str] = Field(default=None, min_length=2, max_length=100)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    subject: str
    grade: Optional[str] = None
    stream: Optional[str] = None
    medium: Optional[str] = None
    file_url: Optional[str] = None
    user_id: int
    created_at: datetime
    author: Optional[UserOut] = None
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_bookmarked: bool = False


class CommentCreate(BaseModel):
    note_id: int
    comment: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    user_id: int
    comment: str
    created_at: datetime
    user: Optional[UserOut] = None


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    grade: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=100)
    medium: Optional[str] = Field(default=None, max_length=10)


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    grade: Optional[str] = None
    subject: Optional[str] = None
    medium: Optional[str] = None
    creator_id: int
    created_at: datetime
    member_count: int = 0
    is_member: bool = False
    is_admin: bool = False
    join_request_status: Optional[str] = None
    pending_request_count: int = 0


class GroupJoinRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    user_id: int
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    user: Optional[UserOut] = None


class DiscussionCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class DiscussionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    user_id: int
    message: str
    created_at: datetime
    user: Optional[UserOut] = None
