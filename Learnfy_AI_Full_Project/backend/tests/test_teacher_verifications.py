import io
import tempfile
import unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.config.settings import settings
from app.models import academic, auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, subject, teacher_verification, user  # noqa: F401
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.models.teacher_verification import TeacherVerification, VerificationStatus
from app.routes import auth, resources, teacher_verifications
from app.services.auth_service import build_access_token

class TeacherVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
        cls.Session=sessionmaker(bind=cls.engine); cls.temp=tempfile.TemporaryDirectory(); settings.TEACHER_VERIFICATION_DIR=cls.temp.name
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        Base.metadata.drop_all(self.engine);Base.metadata.create_all(self.engine);self.db=self.Session()
        self.teacher=User(name="Pending Teacher",email="pending@example.com",password="hash",role=UserRole.student,is_verified_teacher=False,is_email_verified=True)
        self.student=User(name="Student User",email="student@example.com",password="hash",role=UserRole.student,is_email_verified=True)
        self.admin=User(name="Admin User",email="admin@example.com",password="hash",role=UserRole.admin,is_email_verified=True)
        self.db.add_all([self.teacher,self.student,self.admin]);self.db.commit()
        app=FastAPI();app.include_router(auth.router);app.include_router(teacher_verifications.router);app.include_router(resources.router)
        def override_db(): yield self.db
        app.dependency_overrides[get_db]=override_db;self.client=TestClient(app)
    def tearDown(self): self.db.close()
    def headers(self,user): return {"Authorization":f"Bearer {build_access_token(user)}"}
    def submit(self, content=b"%PDF-1.4\n%%EOF", name="proof.pdf", content_type="application/pdf"):
        return self.client.post("/teacher-verifications",headers=self.headers(self.teacher),data={"full_name":"Pending Teacher","qualification":"BSc Education","institution_name":"Learnfy School","subjects_taught":"Mathematics, Physics","years_of_experience":"5"},files={"proof":(name,io.BytesIO(content),content_type)})
    def test_student_registration_continues_normally(self):
        response=self.client.post("/auth/register",json={"name":"New Student","email":"new-student@example.com","password":"Student1!","confirm_password":"Student1!"})
        self.assertEqual(response.status_code,201);self.assertEqual(response.json()["message"],"Account created successfully. You can now log in.")
        created=self.db.query(User).filter(User.email=="new-student@example.com").one()
        self.assertEqual(created.role,UserRole.student)
        created.is_email_verified=False;self.db.commit()
        logged_in=self.client.post("/auth/login",json={"email":"new-student@example.com","password":"Student1!"})
        self.assertEqual(logged_in.status_code,200);self.assertEqual(logged_in.json()["user"]["role"],"student")
        duplicate=self.client.post("/auth/register",json={"name":"New Student","email":"new-student@example.com","password":"Student1!","confirm_password":"Student1!"})
        self.assertEqual(duplicate.status_code,409)
        privileged=self.client.post("/auth/register",json={"name":"Bad Actor","email":"bad@example.com","password":"Student1!","confirm_password":"Student1!","role":"admin"})
        self.assertEqual(privileged.status_code,422)
    def test_submission_security_authorization_rejection_resubmission_and_approval(self):
        self.assertEqual(self.client.post("/teacher-verifications").status_code,401)
        invalid=self.submit(b"MZ executable","proof.pdf","application/pdf");self.assertEqual(invalid.status_code,400)
        wrong_mime=self.submit(b"%PDF-1.4\n%%EOF","proof.pdf","application/octet-stream");self.assertEqual(wrong_mime.status_code,400)
        oversized=self.submit(b"%PDF-"+b"x"*(5*1024*1024+1));self.assertEqual(oversized.status_code,413)
        created=self.submit();self.assertEqual(created.status_code,201);verification_id=created.json()["id"]
        self.db.refresh(self.teacher);self.assertEqual(self.teacher.role,UserRole.student);self.assertTrue(self.db.query(Notification).filter_by(user_id=self.teacher.id,title="Teacher application submitted").first())
        self.assertEqual(self.submit().status_code,409)
        denied=self.client.post("/resources/",headers=self.headers(self.teacher),data={"title":"x","subject":"Math"});self.assertEqual(denied.status_code,403)
        self.assertEqual(self.client.get("/admin/teacher-verifications",headers=self.headers(self.student)).status_code,403)
        rejected=self.client.post(f"/admin/teacher-verifications/{verification_id}/reject",headers=self.headers(self.admin),json={"reason":"Please provide a clearer letter"});self.assertEqual(rejected.status_code,200);self.assertEqual(rejected.json()["status"],"rejected")
        self.db.refresh(self.teacher);self.assertEqual(self.teacher.role,UserRole.student);self.assertFalse(self.teacher.is_verified_teacher)
        resubmitted=self.submit();self.assertEqual(resubmitted.status_code,201);new_id=resubmitted.json()["id"]
        approved=self.client.post(f"/admin/teacher-verifications/{new_id}/approve",headers=self.headers(self.admin));self.assertEqual(approved.status_code,200)
        self.db.refresh(self.teacher);self.assertEqual(self.teacher.role,UserRole.teacher);self.assertTrue(self.teacher.is_verified_teacher)
        self.assertEqual(self.client.post("/resources/",headers=self.headers(self.teacher),data={"title":"Approved material","subject":"Math"}).status_code,201)
        self.assertEqual(self.client.post(f"/admin/teacher-verifications/{new_id}/approve",headers=self.headers(self.admin)).status_code,409)
        self.assertTrue(all(Path(item.proof_file_path).is_file() for item in self.teacher.teacher_verifications))

    def test_private_documents_and_self_approval_are_forbidden(self):
        created=self.submit();verification_id=created.json()["id"]
        self.assertEqual(self.client.get(f"/teacher-verifications/{verification_id}/document",headers=self.headers(self.teacher)).status_code,200)
        self.assertEqual(self.client.get(f"/teacher-verifications/{verification_id}/document",headers=self.headers(self.student)).status_code,404)
        self.assertEqual(self.client.get(f"/admin/teacher-verifications/{verification_id}/document",headers=self.headers(self.student)).status_code,403)
        own=TeacherVerification(user_id=self.admin.id,full_name=self.admin.name,qualification="MEd",institution_name="Admin School",subjects_taught='["Math"]',grades_taught='["General"]',years_of_experience=2,proof_file_path=self.teacher.teacher_verifications[0].proof_file_path,status=VerificationStatus.pending)
        self.db.add(own);self.db.commit()
        self.assertEqual(self.client.post(f"/admin/teacher-verifications/{own.id}/approve",headers=self.headers(self.admin)).status_code,403)

if __name__=="__main__": unittest.main()
