"""
SQLAlchemy database engine, session factory and declarative base.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.settings import settings

# echo=False in production; set True locally if you want to see generated SQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_compatible_schema():
    """Apply small, additive compatibility fixes that create_all cannot perform.

    Existing deployments created before academic profile fields were introduced
    otherwise fail on every User query because SQLAlchemy selects all mapped columns.
    The operation is repeat-safe and never rewrites or removes user data.
    """
    if engine.dialect.name != "mysql":
        return

    user_columns = {
        "academic_level": "VARCHAR(20) NULL AFTER bio",
        "academic_stream": "VARCHAR(100) NULL AFTER academic_level",
        "academic_subject": "VARCHAR(255) NULL AFTER academic_stream",
        "is_email_verified": "BOOLEAN NOT NULL DEFAULT TRUE AFTER is_verified_teacher",
        "student_verification_status": "ENUM('unverified','pending','verified','rejected') NOT NULL DEFAULT 'unverified' AFTER is_email_verified",
        "student_verified_at": "DATETIME NULL AFTER student_verification_status",
        "student_verified_by": "INT NULL AFTER student_verified_at",
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        if "users" not in table_names:
            return
        existing = {column["name"] for column in inspector.get_columns("users")}
        for column_name, definition in user_columns.items():
            if column_name not in existing:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {definition}"))

        # Keep older installations compatible with grade-aware models. These
        # are nullable, additive fields; no existing learning data is changed.
        content_columns = {
            "notes": {
                "grade": "VARCHAR(50) NULL",
                "stream": "VARCHAR(100) NULL",
                "medium": "VARCHAR(10) NULL",
            },
            "resources": {
                "grade": "VARCHAR(50) NULL",
                "stream": "VARCHAR(100) NULL",
                "medium": "VARCHAR(10) NULL",
            },
            "quizzes": {
                "difficulty": "VARCHAR(20) NOT NULL DEFAULT 'medium'",
                "language": "VARCHAR(5) NOT NULL DEFAULT 'en'",
                "quiz_batch_id": "VARCHAR(36) NULL",
                "grade": "VARCHAR(50) NULL",
                "medium": "VARCHAR(10) NULL",
                "submitted_at": "DATETIME NULL",
            },
            "study_groups": {
                "grade": "VARCHAR(50) NULL",
                "subject": "VARCHAR(100) NULL",
                "medium": "VARCHAR(10) NULL",
            },
        }
        for table_name, columns in content_columns.items():
            if table_name not in table_names:
                continue
            existing_columns = {column["name"] for column in inspect(connection).get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(
                        f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {definition}"
                    ))


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
