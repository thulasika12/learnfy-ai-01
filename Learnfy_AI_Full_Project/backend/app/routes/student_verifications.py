"""Student badge proof submission and admin review."""
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.student_verification import StudentProofStatus, StudentVerification
from app.models.user import StudentVerificationStatus, User, UserRole
from app.utils.dependencies import get_current_user, require_admin
from app.services.audit_service import add_admin_audit
from app.services.file_service import save_upload_file
from app.services.storage_service import file_response

router = APIRouter(tags=["Student Verification"])
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}

def serialize(item):
    return {"id": item.id, "user_id": item.user_id, "student_name": item.applicant.name, "student_email": item.applicant.email,
            "original_filename": item.original_filename, "status": item.status.value if hasattr(item.status, "value") else item.status,
            "rejection_reason": item.rejection_reason, "submitted_at": item.submitted_at, "reviewed_at": item.reviewed_at, "reviewed_by": item.reviewed_by}

def save_proof(upload: UploadFile):
    original = Path(upload.filename or "").name[:255]
    path = save_upload_file(upload, category="private/student-verifications", allowed_extensions=ALLOWED_EXTENSIONS,
        max_mb=settings.STUDENT_VERIFICATION_MAX_MB, private=True, local_root=settings.STUDENT_VERIFICATION_DIR)
    return str(path), original

@router.get("/student-verifications/me")
def my_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(StudentVerification).filter(StudentVerification.user_id == user.id).order_by(StudentVerification.submitted_at.desc()).first()
    return serialize(item) if item else {"status": user.student_verification_status.value if hasattr(user.student_verification_status, "value") else user.student_verification_status}

@router.post("/student-verifications", status_code=201)
def submit(proof: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != UserRole.student: raise HTTPException(403, "Only students can submit proof")
    if db.query(StudentVerification).filter(StudentVerification.user_id == user.id, StudentVerification.status == StudentProofStatus.pending).first(): raise HTTPException(409, "A verification is already pending")
    if user.student_verification_status == StudentVerificationStatus.verified: raise HTTPException(409, "Student is already verified")
    path, original = save_proof(proof)
    item = StudentVerification(user_id=user.id, proof_file_path=path, original_filename=original)
    user.student_verification_status = StudentVerificationStatus.pending
    db.add(item); db.commit(); db.refresh(item)
    return serialize(item)

@router.get("/admin/student-verifications")
def admin_list(status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    query = db.query(StudentVerification)
    if status_filter:
        if status_filter not in {x.value for x in StudentProofStatus}: raise HTTPException(400, "Invalid status")
        query = query.filter(StudentVerification.status == status_filter)
    return [serialize(x) for x in query.order_by(StudentVerification.submitted_at.desc()).all()]

@router.get("/admin/student-verifications/{item_id}/document")
def document(item_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.query(StudentVerification).filter(StudentVerification.id == item_id).first()
    if not item: raise HTTPException(404, "Document not found")
    return file_response(item.proof_file_path, filename=item.original_filename, local_root=settings.STUDENT_VERIFICATION_DIR)

@router.post("/admin/student-verifications/{item_id}/approve")
def approve(item_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item = db.query(StudentVerification).filter(StudentVerification.id == item_id, StudentVerification.status == StudentProofStatus.pending).first()
    if not item: raise HTTPException(404, "Pending verification not found")
    now = datetime.now(timezone.utc); item.status = StudentProofStatus.verified; item.reviewed_at = now; item.reviewed_by = admin.id
    item.applicant.student_verification_status = StudentVerificationStatus.verified; item.applicant.student_verified_at = now; item.applicant.student_verified_by = admin.id
    add_admin_audit(db, admin.id, "student_verification.approve", "student_verification", item.id, item.applicant.email)
    db.commit(); db.refresh(item); return serialize(item)

@router.post("/admin/student-verifications/{item_id}/reject")
def reject(item_id: int, payload: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 3 or len(reason) > 1000: raise HTTPException(400, "A rejection reason is required")
    item = db.query(StudentVerification).filter(StudentVerification.id == item_id, StudentVerification.status == StudentProofStatus.pending).first()
    if not item: raise HTTPException(404, "Pending verification not found")
    item.status = StudentProofStatus.rejected; item.rejection_reason = reason; item.reviewed_at = datetime.now(timezone.utc); item.reviewed_by = admin.id
    item.applicant.student_verification_status = StudentVerificationStatus.rejected
    add_admin_audit(db, admin.id, "student_verification.reject", "student_verification", item.id, reason)
    db.commit(); db.refresh(item); return serialize(item)
