import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.models import auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, subject, user  # noqa: F401
from app.models.subject import Subject, SubjectStream
from app.models.user import User, UserRole
from app.routes import subjects
from app.utils.dependencies import require_admin

class SubjectApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine)
    def setUp(self):
        Base.metadata.drop_all(self.engine); Base.metadata.create_all(self.engine); self.db = self.Session()
        self.admin = User(name="Admin", email="subjects-admin@example.com", password="x", role=UserRole.admin)
        self.db.add(self.admin); self.db.commit()
        app = FastAPI(); app.include_router(subjects.router)
        def override_db(): yield self.db
        app.dependency_overrides[get_db] = override_db; app.dependency_overrides[require_admin] = lambda: self.admin
        self.client = TestClient(app)
        for code, name, streams in [("20", "Information and Communication Technology", ["Physical Science", "Commerce", "Engineering Technology", "Bio Systems Technology"]), ("65", "Engineering Technology", ["Engineering Technology"]), ("66", "Bio Systems Technology", ["Bio Systems Technology"]), ("67", "Science for Technology", ["Engineering Technology", "Bio Systems Technology"])]:
            item = Subject(level="AL", stream=streams[0], subject_code=code, name_en=name, name_ta=f"TA {name}", name_si=f"SI {name}", sort_order=int(code)); item.stream_links = [SubjectStream(stream=value) for value in streams]; self.db.add(item)
        self.db.commit()
    def tearDown(self): self.db.close()
    def test_every_technology_stream_and_localized_names(self):
        engineering = self.client.get("/subjects", params={"level": "AL", "stream": "Engineering Technology"})
        self.assertEqual(engineering.status_code, 200); self.assertEqual({x["subject_code"] for x in engineering.json()}, {"20", "65", "67"})
        bio = self.client.get("/subjects", params={"level": "AL", "stream": "Bio Systems Technology"}).json()
        self.assertEqual({x["subject_code"] for x in bio}, {"20", "66", "67"}); self.assertTrue(all(x["name_ta"] and x["name_si"] for x in bio))
    def test_duplicate_code_and_admin_protection(self):
        payload = {"level":"AL","stream":"Commerce","streams":["Commerce"],"subject_code":"20","name_en":"Duplicate","name_ta":"Duplicate","name_si":"Duplicate"}
        self.assertEqual(self.client.post("/admin/subjects", json=payload).status_code, 409)
        unprotected = FastAPI(); unprotected.include_router(subjects.router); unprotected.dependency_overrides[get_db] = lambda: self.db
        self.assertEqual(TestClient(unprotected).post("/admin/subjects", json=payload).status_code, 401)
    def test_inactive_subject_is_hidden_publicly(self):
        item = self.db.query(Subject).filter(Subject.subject_code == "65").first(); item.is_active = False; self.db.commit()
        self.assertNotIn("65", {x["subject_code"] for x in self.client.get("/subjects").json()})

if __name__ == "__main__": unittest.main()
