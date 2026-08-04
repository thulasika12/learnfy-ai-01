"""Study groups with creator-admin ownership and approved membership."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.models.group import GroupDiscussion, GroupJoinRequest, GroupMember, StudyGroup
from app.models.user import User
from app.schemas.note_schema import (
    DiscussionCreate,
    DiscussionOut,
    GroupCreate,
    GroupJoinRequestOut,
    GroupOut,
)
from app.utils.dependencies import get_current_user, get_optional_current_user

router = APIRouter(prefix="/groups", tags=["Study Groups"])


def _serialize_group(group: StudyGroup, current_user: Optional[User] = None) -> GroupOut:
    data = GroupOut.model_validate(group)
    data.member_count = len(group.members)
    membership = next(
        (member for member in group.members if current_user and member.user_id == current_user.id),
        None,
    )
    data.is_member = membership is not None
    data.is_admin = bool(
        current_user
        and (
            group.creator_id == current_user.id
            or (membership is not None and membership.role == "admin")
        )
    )
    if current_user and not data.is_member:
        join_request = next(
            (request for request in group.join_requests if request.user_id == current_user.id),
            None,
        )
        data.join_request_status = join_request.status if join_request else None
    if data.is_admin:
        data.pending_request_count = sum(
            request.status == "pending" for request in group.join_requests
        )
    return data


def _get_group_or_404(db: Session, group_id: int) -> StudyGroup:
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Study group not found")
    return group


def _require_group_admin(db: Session, group: StudyGroup, current_user: User) -> None:
    membership = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group.id,
            GroupMember.user_id == current_user.id,
            GroupMember.role == "admin",
        )
        .first()
    )
    if group.creator_id != current_user.id and not membership:
        raise HTTPException(
            status_code=403,
            detail="Only the group admin can perform this action",
        )


@router.post("/create", response_model=GroupOut, status_code=201)
def create_group(
    payload: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = StudyGroup(name=payload.name, description=payload.description, grade=payload.grade, subject=payload.subject, medium=payload.medium, creator_id=current_user.id)
    db.add(group)
    db.flush()

    # Save the group and its creator-admin membership in one transaction.
    db.add(GroupMember(group_id=group.id, user_id=current_user.id, role="admin"))
    db.commit()
    group = (
        db.query(StudyGroup)
        .options(joinedload(StudyGroup.members), joinedload(StudyGroup.join_requests))
        .filter(StudyGroup.id == group.id)
        .first()
    )
    return _serialize_group(group, current_user)


@router.get("/", response_model=list[GroupOut])
def list_groups(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    groups = (
        db.query(StudyGroup)
        .options(joinedload(StudyGroup.members), joinedload(StudyGroup.join_requests))
        .all()
    )
    return [_serialize_group(g, current_user) for g in groups]


@router.delete("/{group_id}", status_code=200)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = _get_group_or_404(db, group_id)
    _require_group_admin(db, group, current_user)
    db.delete(group)
    db.commit()
    return {"message": "Study group deleted successfully"}


@router.post("/{group_id}/join", status_code=200)
def join_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_group_or_404(db, group_id)

    existing = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        .first()
    )
    if existing:
        return {"message": "Already a member of this group", "status": "approved"}

    join_request = (
        db.query(GroupJoinRequest)
        .filter(
            GroupJoinRequest.group_id == group_id,
            GroupJoinRequest.user_id == current_user.id,
        )
        .first()
    )
    if join_request and join_request.status == "pending":
        return {"message": "Your join request is already pending", "status": "pending"}

    if join_request:
        join_request.status = "pending"
        join_request.created_at = datetime.now(timezone.utc)
        join_request.reviewed_at = None
    else:
        db.add(
            GroupJoinRequest(
                group_id=group_id,
                user_id=current_user.id,
                status="pending",
            )
        )
    db.commit()
    return {"message": "Join request sent to the group admin", "status": "pending"}


@router.get("/{group_id}/join-requests", response_model=list[GroupJoinRequestOut])
def list_join_requests(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = _get_group_or_404(db, group_id)
    _require_group_admin(db, group, current_user)
    return (
        db.query(GroupJoinRequest)
        .options(joinedload(GroupJoinRequest.user))
        .filter(
            GroupJoinRequest.group_id == group_id,
            GroupJoinRequest.status == "pending",
        )
        .order_by(GroupJoinRequest.created_at.asc())
        .all()
    )


@router.post(
    "/{group_id}/join-requests/{request_id}/approve",
    response_model=GroupJoinRequestOut,
)
def approve_join_request(
    group_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = _get_group_or_404(db, group_id)
    _require_group_admin(db, group, current_user)
    join_request = (
        db.query(GroupJoinRequest)
        .options(joinedload(GroupJoinRequest.user))
        .filter(
            GroupJoinRequest.id == request_id,
            GroupJoinRequest.group_id == group_id,
        )
        .first()
    )
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if join_request.status != "pending":
        raise HTTPException(status_code=409, detail="Join request has already been reviewed")

    membership = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == join_request.user_id,
        )
        .first()
    )
    if not membership:
        db.add(
            GroupMember(
                group_id=group_id,
                user_id=join_request.user_id,
                role="member",
            )
        )
    join_request.status = "approved"
    join_request.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(join_request)
    return join_request


@router.post(
    "/{group_id}/join-requests/{request_id}/reject",
    response_model=GroupJoinRequestOut,
)
def reject_join_request(
    group_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = _get_group_or_404(db, group_id)
    _require_group_admin(db, group, current_user)
    join_request = (
        db.query(GroupJoinRequest)
        .options(joinedload(GroupJoinRequest.user))
        .filter(
            GroupJoinRequest.id == request_id,
            GroupJoinRequest.group_id == group_id,
        )
        .first()
    )
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if join_request.status != "pending":
        raise HTTPException(status_code=409, detail="Join request has already been reviewed")

    join_request.status = "rejected"
    join_request.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(join_request)
    return join_request


@router.post("/{group_id}/leave", status_code=200)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = _get_group_or_404(db, group_id)
    if group.creator_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="The group admin cannot leave their own group",
        )
    membership = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="You are not a member of this group")
    if membership.role == "admin":
        raise HTTPException(status_code=400, detail="A group admin cannot leave the group")
    db.delete(membership)
    db.commit()
    return {"message": "Left group successfully"}


@router.post("/{group_id}/discussions", response_model=DiscussionOut, status_code=201)
def post_discussion(
    group_id: int,
    payload: DiscussionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_group_or_404(db, group_id)

    is_member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Your join request must be approved before posting",
        )

    discussion = GroupDiscussion(group_id=group_id, user_id=current_user.id, message=payload.message)
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    return discussion


@router.get("/{group_id}/discussions", response_model=list[DiscussionOut])
def get_discussions(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_group_or_404(db, group_id)
    membership = (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Your join request must be approved before viewing discussions",
        )
    discussions = (
        db.query(GroupDiscussion)
        .options(joinedload(GroupDiscussion.user))
        .filter(GroupDiscussion.group_id == group_id)
        .order_by(GroupDiscussion.created_at.asc())
        .all()
    )
    return discussions
