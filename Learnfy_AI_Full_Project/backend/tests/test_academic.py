import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.models import academic, auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, subject, user  # noqa: F401
from app.models.academic import EducationLevel, Grade, GradeSubject
from app.models.subject import Subject
from app.routes import academic as academic_routes, subjects

class AcademicStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);cls.Session=sessionmaker(bind=cls.engine)
    def setUp(self):
        Base.metadata.drop_all(self.engine);Base.metadata.create_all(self.engine);self.db=self.Session()
        primary=EducationLevel(code="PRIMARY",name_en="Primary",name_ta="ஆரம்பம்",name_si="ප්‍රාථමික",sort_order=1);al=EducationLevel(code="AL",name_en="A/L",name_ta="உயர்தரம்",name_si="උසස් පෙළ",sort_order=2);self.db.add_all([primary,al]);self.db.flush()
        g1=Grade(level_id=primary.id,code="GRADE_1",name_en="Grade 1",name_ta="தரம் 1",name_si="1 ශ්‍රේණිය",grade_number=1,sort_order=1);g13=Grade(level_id=al.id,code="GRADE_13",name_en="Grade 13",name_ta="தரம் 13",name_si="13 ශ්‍රේණිය",grade_number=13,sort_order=13);self.db.add_all([g1,g13]);self.db.flush()
        simple=Subject(level="PRIMARY",stream="General",subject_code="P03",name_en="Mathematics",name_ta="கணிதம்",name_si="ගණිතය");tech=Subject(level="AL",stream="Engineering Technology",subject_code="65",name_en="Engineering Technology",name_ta="பொறியியல் தொழில்நுட்பம்",name_si="ඉංජිනේරු තාක්ෂණවේදය");self.db.add_all([simple,tech]);self.db.flush();self.db.add_all([GradeSubject(grade_id=g1.id,subject_id=simple.id),GradeSubject(grade_id=g13.id,subject_id=tech.id)]);self.db.commit();self.g1=g1;self.g13=g13
        app=FastAPI();app.include_router(academic_routes.router);app.include_router(subjects.router)
        def override_db():yield self.db
        app.dependency_overrides[get_db]=override_db;self.client=TestClient(app)
    def tearDown(self):self.db.close()
    def test_grade_1_to_13_cascades_and_localized_subjects(self):
        levels=self.client.get("/academic/levels").json();self.assertEqual({x["code"] for x in levels},{"PRIMARY","AL"})
        self.assertEqual(self.client.get("/subjects",params={"grade_id":self.g1.id}).json()[0]["name_ta"],"கணிதம்")
        self.assertEqual(self.client.get("/subjects",params={"grade_id":self.g13.id}).json()[0]["subject_code"],"65")

if __name__=="__main__":unittest.main()
