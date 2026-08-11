from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.models import academic, auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, subject, user  # noqa:F401
from app.models.academic import EducationLevel, Grade, GradeSubject
from app.models.subject import Subject
from app.models.user import User, UserRole
from app.routes import users
from app.utils.dependencies import get_current_user


def onboarding_client(role=UserRole.student):
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(engine);db=sessionmaker(bind=engine)()
    level=EducationLevel(code="AL",name_en="G.C.E. A/L",name_ta="AL",name_si="AL",is_active=True);db.add(level);db.flush()
    grade=Grade(level_id=level.id,code="GRADE_13",name_en="Grade 13",name_ta="13",name_si="13",grade_number=13,is_active=True);db.add(grade);db.flush()
    stream=academic.AcademicStream(code="TECH",name_en="Engineering Technology",name_ta="Tech",name_si="Tech",is_active=True);db.add(stream);db.flush()
    item=Subject(level="AL",stream="Engineering Technology",subject_code="65",name_en="Engineering Technology",name_ta="Tech",name_si="Tech",is_active=True);db.add(item);db.flush();db.add(GradeSubject(grade_id=grade.id,subject_id=item.id,medium="all"))
    account=User(name="Applicant",email="applicant@test.dev",password="x",role=role,is_email_verified=True,onboarding_completed=False);db.add(account);db.commit()
    app=FastAPI();app.include_router(users.router)
    def override_db(): yield db
    app.dependency_overrides[get_db]=override_db;app.dependency_overrides[get_current_user]=lambda: account
    return TestClient(app),db,account,level,grade,stream,item


def test_student_onboarding_saves_profile_and_rotates_tokens():
    client,db,account,level,grade,stream,item=onboarding_client()
    response=client.put("/users/onboarding",json={"role":"student","education_level_id":level.id,"grade_id":grade.id,"stream_id":stream.id,"medium":"en","subject_ids":[item.id],"school_name":"Learnfy School"})
    assert response.status_code==200
    db.refresh(account);assert account.onboarding_completed and account.role==UserRole.student
    assert response.json()["user"]["onboarding_completed"] is True and response.json()["access_token"]
    assert account.academic_profile.grade_id==grade.id


def test_public_onboarding_rejects_admin_role_and_admin_account():
    client,db,account,level,grade,stream,item=onboarding_client()
    payload={"role":"admin","education_level_id":level.id,"grade_id":grade.id,"stream_id":stream.id,"medium":"en","subject_ids":[item.id]}
    assert client.put("/users/onboarding",json=payload).status_code==422
    account.role=UserRole.admin;db.commit();payload["role"]="student"
    assert client.put("/users/onboarding",json=payload).status_code==403


def test_teacher_onboarding_sets_unverified_teacher_and_teaching_preferences():
    client,db,account,level,grade,stream,item=onboarding_client()
    response=client.put("/users/onboarding",json={"role":"teacher","education_level_id":level.id,"grade_id":grade.id,"stream_id":stream.id,"medium":"ta","subject_ids":[item.id],"teacher_grade_ids":[grade.id],"teacher_subject_ids":[item.id]})
    assert response.status_code==200
    db.refresh(account);assert account.role==UserRole.teacher and account.onboarding_completed
    assert account.is_verified_teacher is False
    assert response.json()["user"]["role"]=="teacher"
