"""Security and marking tests for generated quiz attempts."""
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.models import auth_token, chat, flashcard, group, note, notification, payment, quiz, resource, user  # noqa: F401
from app.models.user import User, UserRole
from app.routes import ai
from app.ai.quiz_generator import generate_quiz
from app.utils.dependencies import get_current_user


QUESTIONS = [
    {"question": "Two plus two?", "options": ["1", "2", "3", "4"], "answer": "4"},
    {"question": "Three plus three?", "options": ["3", "5", "6", "7"], "answer": "6"},
]


class QuizApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        self.owner = User(name="Owner", email="quiz-owner@example.com", password="x", role=UserRole.student)
        self.other = User(name="Other", email="quiz-other@example.com", password="x", role=UserRole.student)
        self.db.add_all([self.owner, self.other]); self.db.commit()
        self.current = {"user": self.owner}
        app = FastAPI(); app.include_router(ai.router)
        def override_db():
            yield self.db
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: self.current["user"]
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()

    def generate(self, language="en"):
        with patch("app.routes.ai.generate_quiz", return_value=QUESTIONS):
            response = self.client.post("/ai/generate-quiz", json={
                "subject": "Mathematics", "topic": "Addition", "num_questions": 2,
                "difficulty": "medium", "language": language, "grade": "Grade 10", "medium": "en",
            })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertNotIn("answer", str(body).lower().replace("selected_answer", ""))
        self.assertTrue(all(len(question["options"]) == 4 for question in body["questions"]))
        return body

    def answers(self, generated, first="4", second="6"):
        return {"answers": [
            {"question_id": generated["questions"][0]["id"], "selected_answer": first},
            {"question_id": generated["questions"][1]["id"], "selected_answer": second},
        ]}

    def test_all_correct_and_duplicate_submission(self):
        generated = self.generate()
        payload = self.answers(generated)
        response = self.client.post("/ai/quiz/submit", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["score"], response.json()["percentage"]), (2, 100))
        self.assertEqual(self.client.post("/ai/quiz/submit", json=payload).status_code, 409)

    def test_some_wrong_answers_are_marked_on_server(self):
        response = self.client.post("/ai/quiz/submit", json=self.answers(self.generate(), first="3"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["score"], 1)
        self.assertFalse(response.json()["review"][0]["is_correct"])
        self.assertEqual(response.json()["review"][0]["correct_answer"], "4")

    def test_unanswered_invalid_and_duplicate_question_ids(self):
        generated = self.generate()
        question_id = generated["questions"][0]["id"]
        self.assertEqual(self.client.post("/ai/quiz/submit", json={"answers": [{"question_id": question_id, "selected_answer": "4"}]}).status_code, 400)
        invalid = self.answers(generated); invalid["answers"][0]["selected_answer"] = "not an option"
        self.assertEqual(self.client.post("/ai/quiz/submit", json=invalid).status_code, 400)
        duplicate = {"answers": [{"question_id": question_id, "selected_answer": "4"}] * 2}
        self.assertEqual(self.client.post("/ai/quiz/submit", json=duplicate).status_code, 400)

    def test_another_users_question_is_rejected(self):
        generated = self.generate()
        self.current["user"] = self.other
        self.assertEqual(self.client.post("/ai/quiz/submit", json=self.answers(generated)).status_code, 404)

    def test_supported_quiz_languages(self):
        with patch("app.services.entitlement_service.settings.FREE_QUIZ_LIMIT", 3):
            for language in ("en", "ta", "si"):
                self.assertEqual(self.generate(language)["language"], language)

    def test_empty_generated_questions_returns_controlled_error(self):
        with patch("app.routes.ai.generate_quiz", return_value=[]):
            response = self.client.post("/ai/generate-quiz", json={
                "subject": "Mathematics", "topic": "Addition", "num_questions": 2,
                "difficulty": "medium", "language": "en", "grade": "Grade 10", "medium": "en",
            })
        self.assertEqual(response.status_code, 502)
        self.assertIn("failed validation", response.json()["detail"])

    def test_generated_question_schema_rejects_invalid_options(self):
        malformed = [{"question": "Broken?", "options": [], "answer": "none"}] * 2
        with patch("app.routes.ai.generate_quiz", return_value=malformed):
            response = self.client.post("/ai/generate-quiz", json={
                "subject": "Mathematics", "topic": "Addition", "num_questions": 2,
                "difficulty": "medium", "language": "en", "grade": "Grade 10", "medium": "en",
            })
        self.assertEqual(response.status_code, 502)

    def test_request_validation_error_is_not_a_server_crash(self):
        response = self.client.post("/ai/generate-quiz", json={
            "subject": "Mathematics", "topic": "Addition", "num_questions": 2,
            "difficulty": "medium", "language": "en", "medium": "en",
        })
        self.assertEqual(response.status_code, 422)


class QuizGeminiParserTests(unittest.TestCase):
    def test_json_code_fence_is_accepted(self):
        fenced = f"```json\n{__import__('json').dumps(QUESTIONS)}\n```"
        with patch("app.ai.quiz_generator.chat_completion", return_value=fenced):
            self.assertEqual(generate_quiz("Math", "Addition", 2), QUESTIONS)

    def test_invalid_json_retries_once_then_returns_502(self):
        with patch("app.ai.quiz_generator.chat_completion", return_value="not json") as completion:
            with self.assertRaises(HTTPException) as raised:
                generate_quiz("Math", "Addition", 2)
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(completion.call_count, 2)

    def test_gemini_503_is_preserved(self):
        unavailable = HTTPException(status_code=503, detail="Gemini unavailable")
        with patch("app.ai.quiz_generator.chat_completion", side_effect=unavailable) as completion:
            with self.assertRaises(HTTPException) as raised:
                generate_quiz("Math", "Addition", 2)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(completion.call_count, 1)


if __name__ == "__main__":
    unittest.main()
