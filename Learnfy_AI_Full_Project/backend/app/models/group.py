"""Study group models, memberships, join requests, and discussions."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.config.database import Base


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    grade = Column(String(50), nullable=True, index=True)
    subject = Column(String(100), nullable=True, index=True)
    medium = Column(String(10), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", back_populates="groups_created")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    join_requests = relationship(
        "GroupJoinRequest", back_populates="group", cascade="all, delete-orphan"
    )
    discussions = relationship("GroupDiscussion", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uniq_membership"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="member", server_default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    muted_until = Column(DateTime(timezone=True), nullable=True)

    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")


class GroupJoinRequest(Base):
    __tablename__ = "group_join_requests"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uniq_group_join_request"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    group = relationship("StudyGroup", back_populates="join_requests")
    user = relationship("User", back_populates="group_join_requests")


class GroupDiscussion(Base):
    __tablename__ = "group_discussions"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    reply_to_message_id = Column(Integer, ForeignKey("group_discussions.id", ondelete="SET NULL"), nullable=True)
    message_type = Column(String(20), nullable=False, default="text", server_default="text")
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    attachment_size = Column(Integer, nullable=True)
    learning_resource_type = Column(String(20), nullable=True)
    learning_resource_id = Column(Integer, nullable=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("StudyGroup", back_populates="discussions")
    user = relationship("User")
    reply_to = relationship("GroupDiscussion", remote_side=[id])
    reactions = relationship("GroupMessageReaction", cascade="all, delete-orphan")

class GroupMessageReaction(Base):
    __tablename__ = "group_message_reactions"
    __table_args__ = (UniqueConstraint("message_id", "user_id", "emoji", name="uniq_group_message_reaction"),)
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("group_discussions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    emoji = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GroupMessageRead(Base):
    __tablename__ = "group_message_reads"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uniq_group_message_read"),)
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_read_message_id = Column(Integer, ForeignKey("group_discussions.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class GroupMessageReport(Base):
    __tablename__ = "group_message_reports"
    __table_args__ = (UniqueConstraint("message_id", "reporter_id", name="uniq_group_message_report"),)
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("group_discussions.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
