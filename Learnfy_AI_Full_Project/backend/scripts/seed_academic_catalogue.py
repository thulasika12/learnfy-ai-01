"""Idempotently seed Learnfy's production-safe academic reference catalogue."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect

from app.config.database import SessionLocal, engine
from app.models.academic import AcademicStream, EducationLevel, Grade, GradeSubject
from app.models.subject import Subject, SubjectStream


LEVELS = [
    ("PRIMARY", "Primary (Grades 1-5)", "ஆரம்ப நிலை (தரம் 1-5)", "ප්‍රාථමික (1-5 ශ්‍රේණි)", 10),
    ("JUNIOR", "Junior Secondary (Grades 6-9)", "கனிஷ்ட இடைநிலை (தரம் 6-9)", "කනිෂ්ඨ ද්විතීයික (6-9 ශ්‍රේණි)", 20),
    ("OL", "G.C.E. O/L (Grades 10-11)", "க.பொ.த. சாதாரண தரம் (10-11)", "අ.පො.ස. සාමාන්‍ය පෙළ (10-11)", 30),
    ("AL", "G.C.E. A/L (Grades 12-13)", "க.பொ.த. உயர்தரம் (12-13)", "අ.පො.ස. උසස් පෙළ (12-13)", 40),
    ("UNIVERSITY", "University / College", "பல்கலைக்கழகம் / கல்லூரி", "විශ්වවිද්‍යාලය / විද්‍යාලය", 50),
    ("SELF", "Online / Self-directed Learner", "இணைய / சுய கற்றல்", "මාර්ගගත / ස්වයං අධ්‍යයනය", 60),
]

STREAMS = [
    ("BIO", "Biological Science"), ("PHYSICAL", "Physical Science"),
    ("COMMERCE", "Commerce"), ("ARTS", "Arts"),
    ("ENGINEERING_TECH", "Engineering Technology"),
    ("BIO_SYSTEMS_TECH", "Bio Systems Technology"),
    ("COMMON", "General/Common Subjects"),
]

# level, code, English, Tamil, Sinhala, streams
SUBJECTS = [
    ("PRIMARY", "P-LANG", "First Language", "முதல் மொழி", "පළමු භාෂාව", ["General"]),
    ("PRIMARY", "P-ENG", "English", "ஆங்கிலம்", "ඉංග්‍රීසි", ["General"]),
    ("PRIMARY", "P-MATH", "Mathematics", "கணிதம்", "ගණිතය", ["General"]),
    ("PRIMARY", "P-ENV", "Environmental Studies", "சுற்றாடல் கல்வி", "පරිසර අධ්‍යයනය", ["General"]),
    ("PRIMARY", "P-REL", "Religion", "சமயம்", "ආගම", ["General"]),
    ("JUNIOR", "J-LANG", "First Language", "முதல் மொழி", "පළමු භාෂාව", ["General"]),
    ("JUNIOR", "J-ENG", "English", "ஆங்கிலம்", "ඉංග්‍රීසි", ["General"]),
    ("JUNIOR", "J-MATH", "Mathematics", "கணிதம்", "ගණිතය", ["General"]),
    ("JUNIOR", "J-SCI", "Science", "விஞ்ஞானம்", "විද්‍යාව", ["General"]),
    ("JUNIOR", "J-HIST", "History", "வரலாறு", "ඉතිහාසය", ["General"]),
    ("JUNIOR", "J-GEO", "Geography", "புவியியல்", "භූගෝල විද්‍යාව", ["General"]),
    ("JUNIOR", "J-CIV", "Civic Education", "குடியியல் கல்வி", "පුරවැසි අධ්‍යාපනය", ["General"]),
    ("JUNIOR", "J-ICT", "Information and Communication Technology", "தகவல் தொடர்பாடல் தொழில்நுட்பம்", "තොරතුරු හා සන්නිවේදන තාක්ෂණය", ["General"]),
    ("JUNIOR", "J-REL", "Religion", "சமயம்", "ආගම", ["General"]),
    ("OL", "O-LANG", "First Language", "முதல் மொழி", "පළමු භාෂාව", ["General"]),
    ("OL", "O-ENG", "English", "ஆங்கிலம்", "ඉංග්‍රීසි", ["General"]),
    ("OL", "O-MATH", "Mathematics", "கணிதம்", "ගණිතය", ["General"]),
    ("OL", "O-SCI", "Science", "விஞ்ஞானம்", "විද්‍යාව", ["General"]),
    ("OL", "O-HIST", "History", "வரலாறு", "ඉතිහාසය", ["General"]),
    ("OL", "O-ICT", "Information and Communication Technology", "தகவல் தொடர்பாடல் தொழில்நுட்பம்", "තොරතුරු හා සන්නිවේදන තාක්ෂණය", ["General"]),
    ("OL", "O-BUS", "Business and Accounting Studies", "வணிகமும் கணக்கீடும்", "ව්‍යාපාර හා ගිණුම්කරණ අධ්‍යයනය", ["General"]),
    ("OL", "O-REL", "Religion", "சமயம்", "ආගම", ["General"]),
    ("AL", "A-BIO", "Biology", "உயிரியல்", "ජීව විද්‍යාව", ["Biological Science"]),
    ("AL", "A-CHEM", "Chemistry", "இரசாயனவியல்", "රසායන විද්‍යාව", ["Biological Science", "Physical Science"]),
    ("AL", "A-PHY", "Physics", "பௌதிகவியல்", "භෞතික විද්‍යාව", ["Biological Science", "Physical Science"]),
    ("AL", "A-CMATH", "Combined Mathematics", "இணைந்த கணிதம்", "සංයුක්ත ගණිතය", ["Physical Science"]),
    ("AL", "A-ACC", "Accounting", "கணக்கியல்", "ගිණුම්කරණය", ["Commerce"]),
    ("AL", "A-BUS", "Business Studies", "வணிகக் கல்வி", "ව්‍යාපාර අධ්‍යයනය", ["Commerce"]),
    ("AL", "A-ECO", "Economics", "பொருளியல்", "ආර්ථික විද්‍යාව", ["Commerce", "Arts"]),
    ("AL", "A-ICT", "Information and Communication Technology", "தகவல் தொடர்பாடல் தொழில்நுட்பம்", "තොරතුරු හා සන්නිවේදන තාක්ෂණය", ["Physical Science", "Commerce", "Engineering Technology", "Bio Systems Technology"]),
    ("AL", "A-ET", "Engineering Technology", "பொறியியல் தொழில்நுட்பம்", "ඉංජිනේරු තාක්ෂණවේදය", ["Engineering Technology"]),
    ("AL", "A-BST", "Bio Systems Technology", "உயிர்முறைமை தொழில்நுட்பம்", "ජෛව පද්ධති තාක්ෂණවේදය", ["Bio Systems Technology"]),
    ("AL", "A-SFT", "Science for Technology", "தொழில்நுட்பத்திற்கான விஞ்ஞானம்", "තාක්ෂණවේදය සඳහා විද්‍යාව", ["Engineering Technology", "Bio Systems Technology"]),
    ("AL", "A-AGRI", "Agricultural Science", "விவசாய விஞ்ஞானம்", "කෘෂි විද්‍යාව", ["Biological Science", "Bio Systems Technology"]),
    ("AL", "A-HIST", "History", "வரலாறு", "ඉතිහාසය", ["Arts"]),
    ("AL", "A-GEO", "Geography", "புவியியல்", "භූගෝල විද්‍යාව", ["Arts"]),
    ("AL", "A-POL", "Political Science", "அரசியல் விஞ்ஞானம்", "දේශපාලන විද්‍යාව", ["Arts"]),
    ("AL", "A-LOGIC", "Logic and Scientific Method", "தர்க்கமும் விஞ்ஞான முறையும்", "තර්ක ශාස්ත්‍රය හා විද්‍යාත්මක ක්‍රමය", ["Arts"]),
    ("AL", "A-GENENG", "General English", "பொது ஆங்கிலம்", "සාමාන්‍ය ඉංග්‍රීසි", ["General/Common Subjects"]),
    ("AL", "A-GIT", "General Information Technology", "பொது தகவல் தொழில்நுட்பம்", "සාමාන්‍ය තොරතුරු තාක්ෂණය", ["General/Common Subjects"]),
    ("UNIVERSITY", "U-CS", "Computer Science", "கணினி விஞ்ஞானம்", "පරිගණක විද්‍යාව", ["General"]),
    ("UNIVERSITY", "U-IT", "Information Technology", "தகவல் தொழில்நுட்பம்", "තොරතුරු තාක්ෂණය", ["General"]),
    ("UNIVERSITY", "U-ENG", "Engineering", "பொறியியல்", "ඉංජිනේරු විද්‍යාව", ["General"]),
    ("UNIVERSITY", "U-BUS", "Business and Management", "வணிகமும் முகாமைத்துவமும்", "ව්‍යාපාර හා කළමනාකරණය", ["General"]),
    ("UNIVERSITY", "U-MED", "Medicine and Health Sciences", "மருத்துவமும் சுகாதார விஞ்ஞானமும்", "වෛද්‍ය හා සෞඛ්‍ය විද්‍යා", ["General"]),
    ("UNIVERSITY", "U-LAW", "Law", "சட்டம்", "නීතිය", ["General"]),
    ("UNIVERSITY", "U-ARTS", "Arts and Humanities", "கலையும் மானுடவியலும்", "කලා හා මානව ශාස්ත්‍ර", ["General"]),
    ("UNIVERSITY", "U-SCI", "Natural Sciences", "இயற்கை விஞ்ஞானங்கள்", "ස්වාභාවික විද්‍යා", ["General"]),
    ("UNIVERSITY", "U-EDU", "Education", "கல்வியியல்", "අධ්‍යාපනය", ["General"]),
    ("SELF", "S-LANG", "Language Learning", "மொழிக் கற்றல்", "භාෂා ඉගෙනීම", ["General"]),
    ("SELF", "S-PROG", "Programming", "நிரலாக்கம்", "ක්‍රමලේඛනය", ["General"]),
    ("SELF", "S-DATA", "Data Science", "தரவு விஞ்ஞானம்", "දත්ත විද්‍යාව", ["General"]),
    ("SELF", "S-BUS", "Business Skills", "வணிகத் திறன்கள்", "ව්‍යාපාර කුසලතා", ["General"]),
    ("SELF", "S-EXAM", "Exam Preparation", "பரீட்சைத் தயாரிப்பு", "විභාග සූදානම", ["General"]),
    ("SELF", "S-PDEV", "Personal Development", "தனிநபர் மேம்பாடு", "පුද්ගල සංවර්ධනය", ["General"]),
]


def seed_catalogue(db) -> dict[str, int]:
    created = {"levels": 0, "grades": 0, "streams": 0, "subjects": 0, "stream_links": 0, "grade_links": 0}
    levels = {}
    for code, en, ta, si, order in LEVELS:
        item = db.query(EducationLevel).filter_by(code=code).one_or_none()
        if item is None:
            item = EducationLevel(code=code, name_en=en, name_ta=ta, name_si=si, sort_order=order, is_active=True)
            db.add(item); db.flush(); created["levels"] += 1
        levels[code] = item

    grades = {}
    for number in range(1, 14):
        level_code = "PRIMARY" if number <= 5 else "JUNIOR" if number <= 9 else "OL" if number <= 11 else "AL"
        code = f"GRADE_{number}"
        item = db.query(Grade).filter_by(code=code).one_or_none()
        if item is None:
            item = Grade(level_id=levels[level_code].id, code=code, name_en=f"Grade {number}", name_ta=f"தரம் {number}", name_si=f"{number} ශ්‍රේණිය", grade_number=number, sort_order=number, is_active=True)
            db.add(item); db.flush(); created["grades"] += 1
        grades[number] = item

    for order, (code, name) in enumerate(STREAMS, 1):
        if db.query(AcademicStream).filter_by(code=code).one_or_none() is None:
            db.add(AcademicStream(code=code, name_en=name, name_ta=name, name_si=name, sort_order=order, is_active=True)); created["streams"] += 1
    db.flush()

    grade_numbers = {"PRIMARY": range(1, 6), "JUNIOR": range(6, 10), "OL": range(10, 12), "AL": range(12, 14)}
    for order, (level, code, en, ta, si, streams) in enumerate(SUBJECTS, 1):
        item = db.query(Subject).filter_by(level=level, subject_code=code).one_or_none()
        if item is None:
            item = Subject(level=level, stream=streams[0], subject_code=code, name_en=en, name_ta=ta, name_si=si, sort_order=order, is_active=True)
            db.add(item); db.flush(); created["subjects"] += 1
        existing_streams = {link.stream for link in db.query(SubjectStream).filter_by(subject_id=item.id)}
        for stream in streams:
            if stream not in existing_streams:
                db.add(SubjectStream(subject_id=item.id, stream=stream)); created["stream_links"] += 1
        for number in grade_numbers.get(level, []):
            if db.query(GradeSubject).filter_by(grade_id=grades[number].id, subject_id=item.id, medium="all").one_or_none() is None:
                db.add(GradeSubject(grade_id=grades[number].id, subject_id=item.id, medium="all", sort_order=order, is_active=True)); created["grade_links"] += 1
    db.commit()
    return created


def main() -> int:
    required = {"education_levels", "grades", "streams", "subjects", "subject_streams", "grade_subjects"}
    missing = required - set(inspect(engine).get_table_names())
    if missing:
        print(f"Missing tables: {', '.join(sorted(missing))}. Run 'python -m alembic upgrade head' first.")
        return 1
    db = SessionLocal()
    try:
        created = seed_catalogue(db)
        print("Academic catalogue seed complete: " + ", ".join(f"{key}={value}" for key, value in created.items()))
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
