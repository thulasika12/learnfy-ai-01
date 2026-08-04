"""Isolated API and validation tests for the complete flashcard system."""
import io
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.flashcard_generator import generate_flashcard_set
from app.services.ai_service import get_gemini_client
from app.config.settings import settings
from app.config.database import Base, get_db
from app.models import auth_token, chat, flashcard, group, note, payment, quiz, resource, user
from app.models.flashcard import FlashcardSet
from app.models.note import Note
from app.models.user import User, UserRole
from app.routes import flashcards
from app.schemas.flashcard_schema import GeneratedCard, GeneratedSet
from app.utils.dependencies import get_current_user


class FlashcardApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        self.owner = User(name="Owner", email="owner@example.com", password="x", role=UserRole.student)
        self.other = User(name="Other", email="other@example.com", password="x", role=UserRole.student)
        self.db.add_all([self.owner, self.other]); self.db.commit()
        self.current = {"user": self.owner}
        app = FastAPI(); app.include_router(flashcards.router)

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: self.current["user"]
        self.app = app; self.client = TestClient(app)

    def tearDown(self):
        self.db.close()

    def create_set(self):
        response = self.client.post("/flashcards/sets", json={
            "title": "Python Basics", "subject": "ICT", "source_type": "topic",
            "language": "en", "difficulty": "easy", "cards": [
                {"question": "What is a variable?", "answer": "A named value."},
                {"question": "What is a list?", "answer": "An ordered collection."},
            ],
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_generation_validation_and_invalid_ai_response(self):
        response = self.client.post("/flashcards/generate", json={"topic": "", "count": 31})
        self.assertEqual(response.status_code, 422)
        with patch("app.ai.flashcard_generator.chat_completion", return_value="not-json"):
            with self.assertRaises(Exception) as context:
                generate_flashcard_set(title="Test", subject="ICT", count=2, difficulty="easy", language="en")
            self.assertEqual(context.exception.status_code, 502)

    def test_placeholder_ai_key_is_rejected_without_provider_call(self):
        original = settings.GEMINI_API_KEY
        try:
            settings.GEMINI_API_KEY = "PASTE_YOUR_GOOGLE_AI_STUDIO_KEY_HERE"
            with self.assertRaises(Exception) as context:
                get_gemini_client()
            self.assertEqual(context.exception.status_code, 503)
        finally:
            settings.GEMINI_API_KEY = original

    def test_pdf_file_validation(self):
        response = self.client.post(
            "/flashcards/generate-from-pdf",
            data={"title": "Bad file", "subject": "ICT", "count": "3", "difficulty": "easy", "language": "en", "grade": "Grade 8", "medium": "en"},
            files={"file": ("notes.txt", b"plain text", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)

    def generated(self, source_type="topic", source_name=None, language="en", difficulty="easy"):
        return GeneratedSet(
            title="Generated Set", subject="ICT", language=language, difficulty=difficulty,
            source_type=source_type, source_name=source_name,
            cards=[GeneratedCard(question="Question one?", answer="Answer one.")],
        )

    def test_topic_generation_languages_and_difficulties(self):
        for language in ("en", "ta", "si"):
            for difficulty in ("easy", "medium", "hard"):
                with self.subTest(language=language, difficulty=difficulty), patch(
                    "app.routes.flashcards.generate_flashcard_set",
                    return_value=self.generated(language=language, difficulty=difficulty),
                ) as mocked:
                    response = self.client.post("/flashcards/generate", json={
                        "topic": "Python", "subject": "ICT", "count": 1,
                        "language": language, "difficulty": difficulty, "grade": "Grade 8", "medium": language,
                    })
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["language"], language)
                    self.assertEqual(mocked.call_args.kwargs["difficulty"], difficulty)

    def test_valid_pdf_and_saved_note_generation(self):
        from reportlab.pdfgen.canvas import Canvas
        pdf = io.BytesIO(); canvas = Canvas(pdf); canvas.drawString(50, 750, "Python variables store values for later use."); canvas.save()
        with patch("app.routes.flashcards.generate_flashcard_set", return_value=self.generated("pdf", "lesson.pdf")) as mocked:
            response = self.client.post(
                "/flashcards/generate-from-pdf",
                data={"title": "Lesson", "subject": "ICT", "count": "1", "difficulty": "easy", "language": "en", "grade": "Grade 8", "medium": "en"},
                files={"file": ("lesson.pdf", pdf.getvalue(), "application/pdf")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn("Python variables", mocked.call_args.kwargs["source_text"])

        note_record = Note(title="Database Notes", description="A relational database stores structured information in tables.", subject="ICT", user_id=self.owner.id)
        self.db.add(note_record); self.db.commit()
        with patch("app.routes.flashcards.generate_flashcard_set", return_value=self.generated("note", "Database Notes")) as mocked:
            response = self.client.post("/flashcards/generate-from-note", json={"note_id": note_record.id, "count": 1, "difficulty": "medium", "language": "ta"})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn("relational database", mocked.call_args.kwargs["source_text"])

    def test_crud_ownership_and_favourites(self):
        item = self.create_set()
        self.assertEqual(self.client.get(f"/flashcards/sets/{item['id']}").status_code, 200)
        favourite = self.client.patch(f"/flashcards/sets/{item['id']}/favourite")
        self.assertTrue(favourite.json()["is_favourite"])
        card_favourite = self.client.patch(f"/flashcards/cards/{item['cards'][0]['id']}/favourite")
        self.assertTrue(card_favourite.json()["is_favourite"])
        self.current["user"] = self.other
        self.assertEqual(self.client.get(f"/flashcards/sets/{item['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/flashcards/sets/{item['id']}").status_code, 404)

    def test_subject_filter_and_owner_delete(self):
        item = self.create_set()
        filtered = self.client.get("/flashcards/sets", params={"subject": "ICT"})
        self.assertEqual(len(filtered.json()), 1)
        self.assertEqual(self.client.get("/flashcards/sets", params={"subject": "Science"}).json(), [])
        self.assertEqual(self.client.delete(f"/flashcards/sets/{item['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/flashcards/sets/{item['id']}").status_code, 404)

    def test_study_score_calculation(self):
        item = self.create_set(); cards = item["cards"]
        response = self.client.post(f"/flashcards/sets/{item['id']}/study-sessions", json={
            "duration_seconds": 42,
            "answers": [{"card_id": cards[0]["id"], "status": "known"}, {"card_id": cards[1]["id"], "status": "review"}],
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["score_percentage"], 50.0)

    def test_sharing_permissions_and_expiry(self):
        item = self.create_set()
        shared = self.client.post(f"/flashcards/sets/{item['id']}/share", json={"expires_in_days": 7})
        token = shared.json()["share_token"]
        self.assertEqual(self.client.get(f"/flashcards/shared/{token}").status_code, 200)
        record = self.db.query(FlashcardSet).filter_by(id=item["id"]).one()
        record.share_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1); self.db.commit()
        self.assertEqual(self.client.get(f"/flashcards/shared/{token}").status_code, 404)
        self.current["user"] = self.other
        self.assertEqual(self.client.delete(f"/flashcards/sets/{item['id']}/share").status_code, 404)

    def test_csv_export_is_utf8_and_private(self):
        item = self.create_set()
        response = self.client.get(f"/flashcards/sets/{item['id']}/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn("question,answer", response.content.decode("utf-8-sig"))
        self.current["user"] = self.other
        self.assertEqual(self.client.get(f"/flashcards/sets/{item['id']}/export/csv").status_code, 404)

    def test_pdf_export(self):
        item = self.create_set()
        response = self.client.get(f"/flashcards/sets/{item['id']}/export/pdf")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_reminder_settings(self):
        saved = self.client.put("/flashcards/reminders", json={
            "is_enabled": True, "reminder_time": "20:30:00", "timezone": "Asia/Colombo"
        })
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertTrue(self.client.get("/flashcards/reminders").json()["is_enabled"])

    def test_unauthorised_access(self):
        self.app.dependency_overrides.pop(get_current_user)
        self.assertEqual(self.client.get("/flashcards/sets").status_code, 401)


if __name__ == "__main__":
    unittest.main()
