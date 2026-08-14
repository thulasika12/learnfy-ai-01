from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base
import app.models  # noqa: F401
from app.models.academic import EducationLevel, Grade, GradeSubject
from app.models.subject import Subject
from scripts.seed_academic_catalogue import seed_catalogue


def test_academic_catalogue_seed_is_complete_and_idempotent():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        first = seed_catalogue(db)
        counts = (
            db.query(EducationLevel).count(),
            db.query(Grade).count(),
            db.query(Subject).count(),
            db.query(GradeSubject).count(),
        )
        second = seed_catalogue(db)

        assert first["levels"] == 6
        assert {item.code for item in db.query(EducationLevel)} == {"PRIMARY", "JUNIOR", "OL", "AL", "UNIVERSITY", "SELF"}
        assert {item.grade_number for item in db.query(Grade)} == set(range(1, 14))
        assert db.query(Subject).filter_by(level="UNIVERSITY").count() > 0
        assert db.query(Subject).filter_by(level="SELF").count() > 0
        assert second == {key: 0 for key in second}
        assert counts == (
            db.query(EducationLevel).count(),
            db.query(Grade).count(),
            db.query(Subject).count(),
            db.query(GradeSubject).count(),
        )
    finally:
        db.close()
