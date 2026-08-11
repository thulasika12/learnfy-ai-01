"""User profile, avatar and account routes."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User, UserRole
from app.models.academic import AcademicStream, EducationLevel, Grade, UserAcademicProfile, UserSubject, TeacherGrade, TeacherSubject
from app.models.subject import Subject
from app.schemas.user_schema import UserOut, UserUpdate, DeleteAccountRequest, OnboardingRequest, Token
from app.services.auth_service import issue_token_pair
from app.services.file_service import save_upload_file
from app.config.security import verify_password
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    db.commit(); db.refresh(current_user)
    return current_user


@router.put("/onboarding", response_model=Token)
def complete_onboarding(payload: OnboardingRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=403, detail="Administrator accounts cannot use public onboarding")
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before completing onboarding")
    level = db.query(EducationLevel).filter(EducationLevel.id == payload.education_level_id, EducationLevel.is_active.is_(True), EducationLevel.code != "TEACHER").first()
    if not level: raise HTTPException(status_code=400, detail="Invalid education level")
    grade = db.query(Grade).filter(Grade.id == payload.grade_id, Grade.level_id == level.id, Grade.is_active.is_(True)).first() if payload.grade_id else None
    if payload.grade_id and not grade: raise HTTPException(status_code=400, detail="Grade does not belong to the selected education level")
    if level.code in {"PRIMARY", "JUNIOR", "OL", "AL"} and not grade: raise HTTPException(status_code=400, detail="Grade is required for this education level")
    stream = db.query(AcademicStream).filter(AcademicStream.id == payload.stream_id, AcademicStream.is_active.is_(True)).first() if payload.stream_id else None
    if payload.stream_id and not stream: raise HTTPException(status_code=400, detail="Invalid academic stream")
    if level.code == "AL" and not stream: raise HTTPException(status_code=400, detail="Stream is required for G.C.E. A/L")
    requested_subjects = set(payload.subject_ids)
    if payload.role == "teacher":
        requested_subjects.update(payload.teacher_subject_ids)
        if not payload.teacher_grade_ids or not payload.teacher_subject_ids: raise HTTPException(status_code=400, detail="Teaching grades and subject specializations are required")
    if db.query(Subject).filter(Subject.id.in_(requested_subjects), Subject.is_active.is_(True)).count() != len(requested_subjects): raise HTTPException(status_code=400, detail="One or more subjects are invalid")
    if payload.role == "teacher" and db.query(Grade).filter(Grade.id.in_(set(payload.teacher_grade_ids)), Grade.is_active.is_(True)).count() != len(set(payload.teacher_grade_ids)): raise HTTPException(status_code=400, detail="One or more teaching grades are invalid")
    profile = current_user.academic_profile or UserAcademicProfile(user_id=current_user.id); db.add(profile)
    profile.education_level_id = level.id; profile.grade_id = grade.id if grade else None; profile.stream_id = stream.id if stream else None
    profile.medium = payload.medium; profile.school_name = payload.school_name; profile.district = payload.district
    db.query(UserSubject).filter(UserSubject.user_id == current_user.id).delete(synchronize_session=False)
    db.query(TeacherGrade).filter(TeacherGrade.user_id == current_user.id).delete(synchronize_session=False)
    db.query(TeacherSubject).filter(TeacherSubject.user_id == current_user.id).delete(synchronize_session=False)
    db.add_all([UserSubject(user_id=current_user.id, subject_id=value) for value in set(payload.subject_ids)])
    if payload.role == "teacher":
        db.add_all([TeacherGrade(user_id=current_user.id, grade_id=value) for value in set(payload.teacher_grade_ids)])
        db.add_all([TeacherSubject(user_id=current_user.id, subject_id=value) for value in set(payload.teacher_subject_ids)])
    current_user.role = UserRole(payload.role); current_user.is_verified_teacher = False; current_user.onboarding_completed = True
    db.commit(); db.refresh(current_user)
    access, refresh = issue_token_pair(db, current_user)
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(current_user))

@router.post("/profile/avatar", response_model=UserOut)
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.profile_image = save_upload_file(file, category="profile", allowed_extensions={".jpg", ".jpeg", ".png", ".webp"})
    db.commit(); db.refresh(current_user)
    return current_user

@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_account(payload: DeleteAccountRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.password, current_user.password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    db.delete(current_user); db.commit()
    return {"message": "Account deleted successfully"}
