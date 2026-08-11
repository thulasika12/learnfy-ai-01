"""Secure administration APIs for users, metrics, moderation, and audit logs."""
from datetime import datetime, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.models.admin_audit import AdminAudit
from app.models.auth_token import AuthToken
from app.models.content_report import ContentReport, ReportStatus
from app.models.group import StudyGroup
from app.models.note import Note
from app.models.payment import Payment, Subscription
from app.models.resource import Resource
from app.models.student_verification import StudentProofStatus, StudentVerification
from app.models.teacher_verification import TeacherVerification, VerificationStatus
from app.models.user import StudentVerificationStatus, User, UserRole
from app.schemas.user_schema import AdminUserActionRequest, UserOut
from app.services.audit_service import add_admin_audit
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
TARGETS = {"note": Note, "resource": Resource, "group": StudyGroup, "user": User}


class ModerationAction(BaseModel):
    action: str
    note: str = Field(min_length=3, max_length=1000)


def ensure_admin_can_change(target: User, admin: User, db: Session) -> None:
    if target.id == admin.id:
        raise HTTPException(403, "Administrators cannot modify their own account")
    active_admins = db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True), User.deleted_at.is_(None)).count()
    if target.role == UserRole.admin and target.is_active and active_admins <= 1:
        raise HTTPException(409, "The final active administrator cannot be modified")


def filtered_users(db: Session, search: str | None, role: UserRole | None, status_filter: str):
    query = db.query(User)
    if status_filter == "active": query = query.filter(User.is_active.is_(True), User.deleted_at.is_(None))
    elif status_filter == "inactive": query = query.filter(or_(User.is_active.is_(False), User.deleted_at.is_not(None)))
    elif status_filter != "all": raise HTTPException(400, "Invalid status filter")
    if search:
        term = f"%{search.strip()}%"; query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))
    if role: query = query.filter(User.role == role)
    return query


@router.get("/users", response_model=list[UserOut])
def list_users(search: str | None = None, role: UserRole | None = None, status_filter: str = Query("active", alias="status"), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return filtered_users(db, search, role, status_filter).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/users/page")
def users_page(search: str | None = None, role: UserRole | None = None, status_filter: str = Query("all", alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=5, le=100), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = filtered_users(db, search, role, status_filter); total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [UserOut.model_validate(item) for item in items], "page": page, "page_size": page_size, "total": total, "pages": ceil(total / page_size) if total else 0}


@router.put("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, payload: AdminUserActionRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target: raise HTTPException(404, "User not found")
    ensure_admin_can_change(target, admin, db)
    target.is_active = False; target.deleted_at = datetime.now(timezone.utc); target.deleted_by = admin.id; target.deletion_reason = payload.reason.strip()
    db.query(AuthToken).filter(AuthToken.user_id == target.id, AuthToken.is_revoked.is_(False)).update({AuthToken.is_revoked: True}, synchronize_session=False)
    add_admin_audit(db, admin.id, "user.deactivate", "user", target.id, target.deletion_reason)
    db.commit(); db.refresh(target); return target


@router.put("/users/{user_id}/restore", response_model=UserOut)
def restore_user(user_id: int, payload: AdminUserActionRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target: raise HTTPException(404, "User not found")
    ensure_admin_can_change(target, admin, db)
    target.is_active = True; target.deleted_at = None; target.deleted_by = None; target.deletion_reason = None
    add_admin_audit(db, admin.id, "user.restore", "user", target.id, payload.reason.strip())
    db.commit(); db.refresh(target); return target


@router.delete("/users/{user_id}", status_code=204)
def permanently_delete_user(user_id: int, payload: AdminUserActionRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target: raise HTTPException(404, "User not found")
    ensure_admin_can_change(target, admin, db)
    add_admin_audit(db, admin.id, "user.delete", "user", target.id, f"{target.email}: {payload.reason.strip()}")
    db.flush()
    db.query(User).filter(User.id == target.id).delete(synchronize_session=False)
    db.commit(); return Response(status_code=204)


@router.get("/notes/reported")
def get_reported_notes(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Note).filter(Note.is_reported.is_(True)).all()


@router.get("/moderation/reports")
def moderation_reports(status_filter: str = Query("pending", alias="status"), target_type: str | None = None, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if status_filter not in {"all", *(item.value for item in ReportStatus)}: raise HTTPException(400, "Invalid report status")
    query = db.query(ContentReport).options(joinedload(ContentReport.reporter))
    if status_filter != "all": query = query.filter(ContentReport.status == status_filter)
    if target_type:
        if target_type not in TARGETS: raise HTTPException(400, "Invalid target type")
        query = query.filter(ContentReport.target_type == target_type)
    result = []
    for report in query.order_by(ContentReport.created_at.desc()).limit(500).all():
        model = TARGETS[report.target_type]; target = db.query(model).filter(model.id == report.target_id).first()
        title = getattr(target, "title", None) or getattr(target, "name", None) or getattr(target, "email", None) or "Deleted content"
        result.append({"id": report.id, "target_type": report.target_type, "target_id": report.target_id, "target_title": title, "reason": report.reason, "status": report.status, "reporter_name": report.reporter.name if report.reporter else None, "resolution_note": report.resolution_note, "created_at": report.created_at, "reviewed_at": report.reviewed_at})
    return result


@router.post("/moderation/reports/{report_id}/action")
def moderate_report(report_id: int, payload: ModerationAction, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if payload.action not in {"dismiss", "hide", "delete"}: raise HTTPException(400, "Invalid moderation action")
    report = db.query(ContentReport).filter(ContentReport.id == report_id, ContentReport.status == ReportStatus.pending).with_for_update().first()
    if not report: raise HTTPException(404, "Pending report not found")
    model = TARGETS.get(report.target_type); target = db.query(model).filter(model.id == report.target_id).first() if model else None
    if payload.action in {"hide", "delete"} and not target: raise HTTPException(404, "Reported content no longer exists")
    if payload.action == "hide":
        if report.target_type == "user":
            ensure_admin_can_change(target, admin, db); target.is_active = False; target.deleted_at = datetime.now(timezone.utc); target.deleted_by = admin.id; target.deletion_reason = payload.note.strip()
        else: target.is_hidden = True
        report.status = ReportStatus.hidden
    elif payload.action == "delete":
        if report.target_type == "user": ensure_admin_can_change(target, admin, db)
        db.delete(target); report.status = ReportStatus.deleted
    else:
        report.status = ReportStatus.dismissed
        if report.target_type == "note" and target:
            remaining = db.query(ContentReport).filter(ContentReport.target_type == "note", ContentReport.target_id == report.target_id, ContentReport.id != report.id, ContentReport.status == ReportStatus.pending).count()
            if not remaining: target.is_reported = False
    report.resolution_note = payload.note.strip(); report.reviewed_by = admin.id; report.reviewed_at = datetime.now(timezone.utc)
    add_admin_audit(db, admin.id, f"moderation.{payload.action}", report.target_type, report.target_id, payload.note.strip())
    db.commit(); return {"status": report.status}


@router.get("/audit-logs")
def audit_logs(search: str | None = None, action: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=5, le=100), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = db.query(AdminAudit, User.name.label("actor_name")).outerjoin(User, User.id == AdminAudit.actor_id)
    if action: query = query.filter(AdminAudit.action == action)
    if search:
        term = f"%{search.strip()}%"; query = query.filter(or_(AdminAudit.action.ilike(term), AdminAudit.target_type.ilike(term), AdminAudit.details.ilike(term), User.name.ilike(term)))
    total = query.count(); rows = query.order_by(AdminAudit.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": item.id, "actor_id": item.actor_id, "actor_name": actor_name or "Deleted administrator", "action": item.action, "target_type": item.target_type, "target_id": item.target_id, "description": item.details, "created_at": item.created_at} for item, actor_name in rows], "page": page, "total": total, "pages": ceil(total / page_size) if total else 0}


@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    active = (User.is_active.is_(True), User.deleted_at.is_(None)); now = datetime.now(timezone.utc)
    return {
        "total_users": db.query(User).filter(*active).count(),
        "total_students": db.query(User).filter(User.role == UserRole.student, *active).count(),
        "total_teachers": db.query(User).filter(User.role == UserRole.teacher, *active).count(),
        "verified_teachers": db.query(User).filter(User.role == UserRole.teacher, User.is_verified_teacher.is_(True), *active).count(),
        "verified_students": db.query(User).filter(User.student_verification_status == StudentVerificationStatus.verified, *active).count(),
        "total_notes": db.query(Note).count(),
        "total_resources": db.query(Resource).count(),
        "total_study_groups": db.query(StudyGroup).count(),
        "pending_teacher_verifications": db.query(TeacherVerification).filter(TeacherVerification.status == VerificationStatus.pending).count(),
        "pending_student_verifications": db.query(StudentVerification).filter(StudentVerification.status == StudentProofStatus.pending).count(),
        "reported_notes": db.query(Note).filter(Note.is_reported.is_(True)).count(),
        "pending_reports": db.query(ContentReport).filter(ContentReport.status == ReportStatus.pending).count(),
        # Select only the primary key for this count. Querying the mapped entity
        # makes SQLAlchemy include every subscription column in the subquery,
        # which breaks statistics on legacy databases that predate optional
        # Stripe metadata columns.
        "active_subscriptions": db.query(Subscription.id).filter(Subscription.status == "active", Subscription.current_period_end > now).count(),
        "successful_payments": db.query(Payment).filter(Payment.status == "success").count(),
    }
