import unittest
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.models import auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, subject, user  # noqa: F401
from app.models.chat import AIChat
from app.models.group import GroupMember, StudyGroup
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.user import User, UserRole
from app.routes import dashboard
from app.utils.dependencies import get_current_user

class DashboardStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine)
    def setUp(self):
        Base.metadata.drop_all(self.engine); Base.metadata.create_all(self.engine); self.db = self.Session()
        self.owner = User(name="Owner", email="dashboard@example.com", password="x", role=UserRole.student)
        self.other = User(name="Other", email="dashboard-other@example.com", password="x", role=UserRole.student)
        self.db.add_all([self.owner, self.other]); self.db.commit()
        app = FastAPI(); app.include_router(dashboard.router)
        def override_db(): yield self.db
        app.dependency_overrides[get_db] = override_db; app.dependency_overrides[get_current_user] = lambda: self.owner
        self.client = TestClient(app)
    def tearDown(self): self.db.close()
    def test_zero_defaults_and_current_user_aggregates(self):
        self.assertEqual(self.client.get("/dashboard/stats").json(), {"uploaded_notes":0,"ai_doubts":0,"study_groups":0,"quizzes_generated":0})
        group_item = StudyGroup(name="Study", creator_id=self.owner.id); self.db.add(group_item); self.db.flush()
        self.db.add_all([
            Note(title="Mine", subject="Physics", user_id=self.owner.id), Note(title="Other", subject="Physics", user_id=self.other.id),
            AIChat(user_id=self.owner.id, question="Q", answer="A"), GroupMember(group_id=group_item.id, user_id=self.owner.id),
            Quiz(user_id=self.owner.id, quiz_batch_id="attempt-1", question="Q1", options='["a","b","c","d"]', answer="a", submitted_at=datetime.now(timezone.utc)),
            Quiz(user_id=self.owner.id, quiz_batch_id="attempt-1", question="Q2", options='["a","b","c","d"]', answer="b", submitted_at=datetime.now(timezone.utc)),
        ]); self.db.commit()
        self.assertEqual(self.client.get("/dashboard/stats").json(), {"uploaded_notes":1,"ai_doubts":1,"study_groups":1,"quizzes_generated":1})

if __name__ == "__main__": unittest.main()
