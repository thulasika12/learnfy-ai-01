from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.academic import AcademicStream, EducationLevel, Grade, UserAcademicProfile, UserSubject, TeacherGrade, TeacherSubject
from app.models.user import User
from app.schemas.academic_schema import AcademicProfileOut, AcademicProfileWrite, GradeOut, LocalizedAcademicOut
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/academic", tags=["Academic Structure"])

@router.get("/levels", response_model=list[LocalizedAcademicOut])
def levels(db: Session = Depends(get_db)):
    # Teacher is an account role, not a learner education-level option.
    return db.query(EducationLevel).filter(
        EducationLevel.is_active.is_(True), EducationLevel.code != "TEACHER"
    ).order_by(EducationLevel.sort_order).all()
@router.get("/grades", response_model=list[GradeOut])
def grades(level_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Grade).filter(Grade.is_active.is_(True));
    if level_id: query = query.filter(Grade.level_id == level_id)
    return query.order_by(Grade.sort_order).all()
@router.get("/streams", response_model=list[LocalizedAcademicOut])
def streams(db: Session = Depends(get_db)): return db.query(AcademicStream).filter(AcademicStream.is_active.is_(True)).order_by(AcademicStream.sort_order).all()

def serialize_profile(db, profile):
    if not profile: return AcademicProfileOut()
    return AcademicProfileOut(education_level_id=profile.education_level_id, grade_id=profile.grade_id, stream_id=profile.stream_id, medium=profile.medium, school_name=profile.school_name, district=profile.district, guardian_consent=profile.guardian_consent,
        subject_ids=[x.subject_id for x in db.query(UserSubject).filter(UserSubject.user_id == profile.user_id)], teacher_grade_ids=[x.grade_id for x in db.query(TeacherGrade).filter(TeacherGrade.user_id == profile.user_id)], teacher_subject_ids=[x.subject_id for x in db.query(TeacherSubject).filter(TeacherSubject.user_id == profile.user_id)])

@router.get("/profile", response_model=AcademicProfileOut)
def get_academic_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)): return serialize_profile(db, user.academic_profile)
@router.put("/profile", response_model=AcademicProfileOut)
def update_academic_profile(payload: AcademicProfileWrite, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.grade_id and not db.query(Grade).filter(Grade.id == payload.grade_id, Grade.is_active.is_(True)).first(): raise HTTPException(400, "Invalid grade")
    profile = user.academic_profile or UserAcademicProfile(user_id=user.id); db.add(profile)
    for field in ("education_level_id","grade_id","stream_id","medium","school_name","district","guardian_consent"): setattr(profile, field, getattr(payload, field))
    db.query(UserSubject).filter(UserSubject.user_id == user.id).delete(); db.query(TeacherGrade).filter(TeacherGrade.user_id == user.id).delete(); db.query(TeacherSubject).filter(TeacherSubject.user_id == user.id).delete()
    db.add_all([UserSubject(user_id=user.id, subject_id=value) for value in set(payload.subject_ids)])
    if str(user.role.value if hasattr(user.role,"value") else user.role) in ("teacher","admin"):
        db.add_all([TeacherGrade(user_id=user.id, grade_id=value) for value in set(payload.teacher_grade_ids)]); db.add_all([TeacherSubject(user_id=user.id, subject_id=value) for value in set(payload.teacher_subject_ids)])
    db.commit(); return serialize_profile(db, profile)
