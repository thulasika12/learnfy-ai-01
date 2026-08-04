"""Teacher verification submission and audited admin review endpoints."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.notification import Notification
from app.models.teacher_verification import TeacherVerification, VerificationStatus
from app.models.user import User, UserRole
from app.schemas.teacher_verification_schema import RejectionRequest, TeacherVerificationOut
from app.utils.dependencies import get_current_user, require_admin
from app.services.audit_service import add_admin_audit

router = APIRouter(tags=["Teacher Verification"])
ALLOWED_EXTENSIONS={".pdf",".jpg",".jpeg",".png"}; ALLOWED_TYPES={"application/pdf","image/jpeg","image/png"}

def parse_values(value: str, field: str) -> list[str]:
    items=[item.strip() for item in value.split(",") if item.strip()]
    if not items or len(items)>30 or any(len(item)>100 for item in items): raise HTTPException(400, f"Invalid {field}")
    return list(dict.fromkeys(items))

def serialize(item: TeacherVerification) -> TeacherVerificationOut:
    return TeacherVerificationOut(id=item.id,user_id=item.user_id,full_name=item.full_name,qualification=item.qualification,institution_name=item.institution_name,
        subjects_taught=json.loads(item.subjects_taught),grades_taught=json.loads(item.grades_taught),years_of_experience=item.years_of_experience,
        official_email=item.official_email,additional_information=item.additional_information,status=item.status.value if hasattr(item.status,"value") else item.status,
        rejection_reason=item.rejection_reason,submitted_at=item.submitted_at,reviewed_at=item.reviewed_at,reviewed_by=item.reviewed_by,has_proof=True,applicant_email=item.applicant.email if item.applicant else None)

def save_private_proof(upload: UploadFile) -> tuple[str,str]:
    original=Path(upload.filename or "").name[:255];suffix=Path(original).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS or upload.content_type not in ALLOWED_TYPES: raise HTTPException(400,"Proof must be a PDF, JPG, JPEG or PNG file")
    limit=settings.TEACHER_VERIFICATION_MAX_MB*1024*1024; content=upload.file.read(limit+1)
    if not content or len(content)>limit: raise HTTPException(413,f"Proof file must not exceed {settings.TEACHER_VERIFICATION_MAX_MB} MB")
    valid=(content.startswith(b"%PDF-") if suffix==".pdf" else content.startswith(b"\x89PNG\r\n\x1a\n") if suffix==".png" else content.startswith(b"\xff\xd8\xff"))
    if not valid: raise HTTPException(400,"Proof file contents do not match its declared type")
    directory=Path(settings.TEACHER_VERIFICATION_DIR).resolve(); directory.mkdir(parents=True,exist_ok=True)
    path=(directory/f"{uuid4().hex}{suffix}").resolve()
    if directory not in path.parents: raise HTTPException(400,"Invalid filename")
    path.write_bytes(content); return str(path),original

@router.post("/teacher-verifications",response_model=TeacherVerificationOut,status_code=201)
def submit_verification(full_name:str=Form(...,min_length=2,max_length=150),qualification:str=Form(...,min_length=2,max_length=255),institution_name:str=Form(...,min_length=2,max_length=255),subjects_taught:str=Form(...),years_of_experience:int=Form(...,ge=0,le=70),grades_taught:str=Form("General"),official_email:str|None=Form(None),additional_information:str|None=Form(None,max_length=2000),proof:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if db.query(TeacherVerification).filter(TeacherVerification.user_id==user.id,TeacherVerification.status==VerificationStatus.pending).first(): raise HTTPException(409,"A pending teacher verification already exists")
    if db.query(TeacherVerification).filter(TeacherVerification.user_id==user.id,TeacherVerification.status==VerificationStatus.approved).first(): raise HTTPException(409,"Teacher account is already approved")
    if user.role != UserRole.student: raise HTTPException(403,"Only active student accounts can apply to become teachers")
    if official_email:
        try: official_email=str(TypeAdapter(EmailStr).validate_python(official_email))
        except ValidationError: raise HTTPException(400,"Invalid official email")
    path,original=save_private_proof(proof); item=TeacherVerification(user_id=user.id,full_name=full_name.strip(),qualification=qualification.strip(),institution_name=institution_name.strip(),subjects_taught=json.dumps(parse_values(subjects_taught,"subjects")),grades_taught=json.dumps(parse_values(grades_taught,"grades")),years_of_experience=years_of_experience,official_email=official_email.strip().lower() if official_email else None,proof_file_path=path,original_filename=original,additional_information=additional_information.strip() if additional_information else None)
    db.add(item)
    db.add(Notification(user_id=user.id,type="teacher_verification",title="Teacher application submitted",message="Your teacher application is pending administrator review.",link="/teacher-verification"))
    try: db.commit()
    except IntegrityError: db.rollback(); Path(path).unlink(missing_ok=True); raise HTTPException(409,"A pending teacher verification already exists")
    db.refresh(item); return serialize(item)

@router.get("/teacher-verifications/me",response_model=TeacherVerificationOut|None)
def my_verification(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(TeacherVerification).filter(TeacherVerification.user_id==user.id).order_by(TeacherVerification.submitted_at.desc()).first(); return serialize(item) if item else None

@router.get("/teacher-verifications/{verification_id}/document")
def applicant_document(verification_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=db.query(TeacherVerification).filter(TeacherVerification.id==verification_id,TeacherVerification.user_id==user.id).first()
    private_root=Path(settings.TEACHER_VERIFICATION_DIR).resolve();proof_path=Path(item.proof_file_path).resolve() if item else None
    if not item or private_root not in proof_path.parents or not proof_path.is_file(): raise HTTPException(404,"Verification document not found")
    return FileResponse(proof_path,filename=item.original_filename or f"teacher-proof-{item.id}{proof_path.suffix}")

@router.get("/admin/teacher-verifications",response_model=list[TeacherVerificationOut])
def admin_list(status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),_:User=Depends(require_admin)):
    query=db.query(TeacherVerification)
    if status_filter:
        if status_filter not in {x.value for x in VerificationStatus}: raise HTTPException(400,"Invalid status")
        query=query.filter(TeacherVerification.status==status_filter)
    return [serialize(item) for item in query.order_by(TeacherVerification.submitted_at.desc()).all()]

@router.get("/admin/teacher-verifications/{verification_id}",response_model=TeacherVerificationOut)
def admin_detail(verification_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    item=db.query(TeacherVerification).filter(TeacherVerification.id==verification_id).first()
    if not item: raise HTTPException(404,"Teacher verification not found")
    return serialize(item)

@router.get("/admin/teacher-verifications/{verification_id}/document")
def admin_document(verification_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    item=db.query(TeacherVerification).filter(TeacherVerification.id==verification_id).first()
    private_root=Path(settings.TEACHER_VERIFICATION_DIR).resolve(); proof_path=Path(item.proof_file_path).resolve() if item else None
    if not item or private_root not in proof_path.parents or not proof_path.is_file(): raise HTTPException(404,"Verification document not found")
    return FileResponse(proof_path,filename=f"teacher-proof-{item.id}{proof_path.suffix}")

def pending_item(db,id):
    item=db.query(TeacherVerification).filter(TeacherVerification.id==id).with_for_update().first()
    if not item: raise HTTPException(404,"Teacher verification not found")
    if item.status != VerificationStatus.pending: raise HTTPException(409,"Teacher verification has already been processed")
    return item

@router.post("/admin/teacher-verifications/{verification_id}/approve",response_model=TeacherVerificationOut)
def approve(verification_id:int,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=pending_item(db,verification_id); applicant=db.query(User).filter(User.id==item.user_id).with_for_update().first()
    if applicant.id==admin.id: raise HTTPException(403,"Administrators cannot approve their own application")
    item.status=VerificationStatus.approved;item.reviewed_by=admin.id;item.reviewed_at=datetime.now(timezone.utc);item.rejection_reason=None;applicant.role=UserRole.teacher;applicant.is_verified_teacher=True
    db.add(Notification(user_id=applicant.id,type="teacher_verification",title="Teacher verification approved",message="Your teacher application has been approved.",link="/teacher/dashboard"));add_admin_audit(db,admin.id,"teacher_verification.approve","teacher_verification",item.id,applicant.email);db.commit();db.refresh(item);return serialize(item)

@router.post("/admin/teacher-verifications/{verification_id}/reject",response_model=TeacherVerificationOut)
def reject(verification_id:int,payload:RejectionRequest,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=pending_item(db,verification_id); applicant=db.query(User).filter(User.id==item.user_id).with_for_update().first();item.status=VerificationStatus.rejected;item.rejection_reason=payload.reason.strip();item.reviewed_by=admin.id;item.reviewed_at=datetime.now(timezone.utc);applicant.role=UserRole.student;applicant.is_verified_teacher=False
    db.add(Notification(user_id=applicant.id,type="teacher_verification",title="Teacher verification needs attention",message="Your teacher application was not approved. Review the reason and resubmit.",link="/teacher-verification"));add_admin_audit(db,admin.id,"teacher_verification.reject","teacher_verification",item.id,payload.reason.strip());db.commit();db.refresh(item);return serialize(item)
