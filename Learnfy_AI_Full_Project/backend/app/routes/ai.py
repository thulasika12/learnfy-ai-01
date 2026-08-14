"""
AI feature routes: doubt-solver chat, note summarizer, quiz generator,
and study planner. All require authentication so usage can be tied to a user.
"""
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.chatbot import solve_doubt
from app.ai.summarizer import summarize_text
from app.ai.quiz_generator import generate_quiz
from app.ai.recommender import generate_study_plan
from app.ai.flashcard_generator import generate_flashcards
from app.config.database import get_db
from app.models.chat import AIChat
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.ai_schema import (
    ChatRequest,
    ChatResponse,
    SummarizeRequest,
    SummarizeResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    GeneratedQuizQuestion,
    QuizQuestion,
    QuizQuestionReview,
    QuizSubmitRequest,
    QuizSubmitResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    Flashcard,
    FlashcardGenerateRequest,
    FlashcardGenerateResponse,
)
from app.services.document_service import extract_text_from_upload
from app.services.entitlement_service import consume, refund
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Features"])


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "ai_chat")
    """AI Doubt Solver — student asks an academic question, AI explains the answer."""
    contextual_question = f"Student grade/level: {payload.grade or 'unspecified'}. Subject: {payload.subject or 'general'}. Learning medium: {payload.medium or 'unspecified'}. Respond in {payload.response_language}. Use age-appropriate, safe language and never exceed the learner's grade level. Question: {payload.question}"
    answer = solve_doubt(contextual_question)

    chat_record = AIChat(user_id=current_user.id, question=payload.question, answer=answer)
    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return ChatResponse(question=payload.question, answer=answer, created_at=chat_record.created_at)


@router.post("/summarize", response_model=SummarizeResponse)
def ai_summarize(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "summary")
    """AI Note Summarizer — accepts raw text (from a pasted note or extracted PDF) and returns a summary."""
    source = f"Student grade/level: {payload.grade or 'unspecified'}. Subject: {payload.subject or 'general'}. Learning medium: {payload.medium or 'unspecified'}. Respond in {payload.response_language}. Produce a grade-appropriate summary.\n\n{payload.text}"
    summary = summarize_text(source, payload.length)
    return SummarizeResponse(summary=summary)


@router.post("/summarize-file", response_model=SummarizeResponse)
def ai_summarize_file(
    file: UploadFile = File(...),
    length: str = Form("medium"),
    subject: str | None = Form(None),
    grade: str | None = Form(None),
    medium: str | None = Form(None),
    response_language: str = Form("en"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "summary")
    """Extract text from a TXT/PDF/DOCX file and summarize it."""
    text = extract_text_from_upload(file)
    source = f"Student grade/level: {grade or 'unspecified'}. Subject: {subject or 'general'}. Learning medium: {medium or 'unspecified'}. Respond in {response_language}. Produce a grade-appropriate summary.\n\n{text}"
    return SummarizeResponse(summary=summarize_text(source, length))


@router.post("/generate-quiz", response_model=QuizGenerateResponse)
def ai_generate_quiz(
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "quiz")
    """AI Quiz Generator — generates MCQ questions for a subject/topic, optionally from note text."""
    try:
        generated = generate_quiz(
            subject=payload.subject,
            topic=payload.topic,
            num_questions=payload.num_questions,
            source_text=payload.source_text,
            language=payload.language,
            difficulty=payload.difficulty,
            grade=payload.grade,
            medium=payload.medium,
        )
        raw_questions = [GeneratedQuizQuestion.model_validate(question).model_dump() for question in generated]
        if len(raw_questions) != payload.num_questions:
            raise ValueError("AI returned an unexpected number of questions")
    except (ValidationError, ValueError) as exc:
        refund(db, current_user.id, "quiz")
        raise HTTPException(status_code=502, detail="The generated quiz failed validation. Please try again.") from exc
    except Exception:
        refund(db, current_user.id, "quiz")
        raise

    questions = []
    batch_id = str(uuid4())
    for q in raw_questions:
        record = Quiz(
            user_id=current_user.id,
            subject=payload.subject,
            topic=payload.topic,
            grade=payload.grade,
            medium=payload.medium,
            difficulty=payload.difficulty,
            language=payload.language,
            quiz_batch_id=batch_id,
            question=q["question"],
            options=json.dumps(q["options"]),
            answer=q["answer"],
        )
        db.add(record)
        db.flush()
        questions.append(
            QuizQuestion(
                id=record.id,
                question=record.question,
                options=q["options"],
            )
        )
    db.commit()

    return QuizGenerateResponse(
        subject=payload.subject,
        topic=payload.topic,
        language=payload.language,
        difficulty=payload.difficulty,
        questions=questions,
    )


@router.post("/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a quiz on the server and reveal correct answers only after submission."""
    question_ids = [answer.question_id for answer in payload.answers]
    if len(question_ids) != len(set(question_ids)):
        raise HTTPException(status_code=400, detail="Each quiz question may be answered only once")

    records = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id, Quiz.id.in_(question_ids))
        .with_for_update()
        .all()
    )
    records_by_id = {record.id: record for record in records}
    if len(records_by_id) != len(question_ids):
        raise HTTPException(status_code=404, detail="One or more quiz questions were not found")

    batch_ids = {record.quiz_batch_id for record in records}
    if None in batch_ids or len(batch_ids) != 1:
        raise HTTPException(status_code=400, detail="Answers must belong to one generated quiz")
    batch_id = next(iter(batch_ids))
    batch_records = db.query(Quiz).filter(
        Quiz.user_id == current_user.id, Quiz.quiz_batch_id == batch_id
    ).with_for_update().all()
    if len(batch_records) != len(question_ids):
        raise HTTPException(status_code=400, detail="Every quiz question must be answered")
    if any(record.submitted_at is not None for record in batch_records):
        raise HTTPException(status_code=409, detail="This quiz has already been submitted")

    score = 0
    review = []
    for submitted in payload.answers:
        record = records_by_id[submitted.question_id]
        options = json.loads(record.options)
        selected_answer = submitted.selected_answer.strip()
        if selected_answer not in options:
            raise HTTPException(
                status_code=400,
                detail="One or more selected answers are invalid",
            )
        is_correct = selected_answer == record.answer
        score += int(is_correct)
        review.append(
            QuizQuestionReview(
                question_id=record.id,
                question=record.question,
                options=options,
                selected_answer=selected_answer,
                correct_answer=record.answer,
                is_correct=is_correct,
            )
        )

    submitted_at = datetime.now(timezone.utc)
    for record in batch_records:
        record.submitted_at = submitted_at
    db.commit()

    total = len(review)
    percentage = round((score / total) * 100, 2)
    return QuizSubmitResponse(
        score=score,
        total=total,
        percentage=percentage,
        review=review,
    )


@router.post("/study-plan", response_model=StudyPlanResponse)
def ai_study_plan(
    payload: StudyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "study_planner")
    """AI Study Planner — creates a personalized day-by-day study schedule."""
    try:
        plan = generate_study_plan(
            subjects=[f"{subject} ({payload.grade or 'unspecified level'}, {payload.medium or 'unspecified medium'}, respond in {payload.response_language})" for subject in payload.subjects],
            hours_per_day=payload.hours_per_day,
            days=payload.days,
            goal=payload.goal,
        )
    except Exception:
        refund(db, current_user.id, "study_planner")
        raise
    return StudyPlanResponse(plan=plan)


@router.post("/flashcards", response_model=FlashcardGenerateResponse)
def ai_flashcards(
    payload: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consume(db, current_user.id, "flashcards")
    cards = [Flashcard(**card) for card in generate_flashcards(payload.topic, payload.count)]
    return FlashcardGenerateResponse(topic=payload.topic, cards=cards)
