"""
Learnfy AI — FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""
import json
import logging
import os
import time

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import text
from app.config.settings import settings
from app.config.database import engine

# Import all models so SQLAlchemy is aware of them before create_all() runs
from app.models import user, note, group, chat, quiz, resource, auth_token, payment, flashcard, notification, subject, academic, teacher_verification, email_verification, student_verification, admin_audit, content_report, entitlement  # noqa: F401

from app.routes import auth, users, notes, comments, groups, group_chat, ai, chat as chat_routes, resources, admin, payments, flashcards, notifications, subjects, dashboard, academic, teacher_verifications, student_verifications, reports, entitlements

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("learnfy")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered learning platform for students and teachers — share notes, "
    "solve doubts with AI, create study groups, and manage learning progress.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the React frontend to call this API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?"
        if settings.ENVIRONMENT.lower() == "development"
        else None
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def structured_request_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    logger.info(json.dumps({"event":"http_request", "method":request.method,
        "path":request.url.path, "status":response.status_code,
        "duration_ms":round((time.perf_counter()-started)*1000, 2)}))
    return response

# ---------------------------------------------------------------------------
# Static files — serve uploaded notes / profile images
# ---------------------------------------------------------------------------
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors[0]["message"] if errors else "Validation error", "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(comments.router)
app.include_router(groups.router)
app.include_router(group_chat.router)
app.include_router(ai.router)
app.include_router(chat_routes.router)
app.include_router(resources.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(flashcards.router)
app.include_router(notifications.router)
app.include_router(subjects.router)
app.include_router(dashboard.router)
app.include_router(academic.router)
app.include_router(teacher_verifications.router)
app.include_router(student_verifications.router)
app.include_router(reports.router)
app.include_router(entitlements.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": f"{settings.APP_NAME} API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.get("/health/live", tags=["Health"])
def health_live():
    return {"status": "ok"}

@app.get("/health/ready", tags=["Health"])
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
