from app.models.notification import Notification  # noqa: F401
from app.models.subject import Subject, SubjectStream  # noqa: F401
from app.models.academic import EducationLevel, Grade, AcademicStream, GradeSubject, UserAcademicProfile, UserSubject, TeacherGrade, TeacherSubject  # noqa: F401
from app.models.teacher_verification import TeacherVerification, VerificationStatus  # noqa: F401
from app.models.email_verification import EmailVerificationCode
from app.models.student_verification import StudentVerification
from app.models.admin_audit import AdminAudit
from app.models.content_report import ContentReport
from app.models.entitlement import DailyAIUsage, StripeEvent
from app.models.user import User
from app.models.note import Note, Comment, Like, Bookmark
from app.models.group import StudyGroup, GroupMember, GroupJoinRequest, GroupDiscussion
from app.models.chat import AIChat
from app.models.quiz import Quiz
from app.models.resource import Resource
from app.models.auth_token import AuthToken
from app.models.payment import Payment, Subscription
from app.models.flashcard import FlashcardSet, Flashcard, FlashcardStudySession, FlashcardSessionAnswer, FlashcardReminder
