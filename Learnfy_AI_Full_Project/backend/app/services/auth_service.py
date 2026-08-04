"""Authentication business logic."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.config.security import hash_password, verify_password, create_access_token, create_opaque_token, hash_token
from app.config.settings import settings
from app.models.user import User
from app.models.auth_token import AuthToken
from app.models.academic import Grade, UserAcademicProfile, UserSubject, TeacherGrade, TeacherSubject
from app.schemas.user_schema import UserRegister, UserLogin


def register_user(db: Session, payload: UserRegister) -> User:
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(name=payload.name, email=email, password=hash_password(payload.password), role="student")
    db.add(user)
    db.flush()
    db.commit(); db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLogin) -> User:
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated")
    return user


def build_access_token(user: User) -> str:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return create_access_token({"sub": str(user.id), "role": role})


def issue_database_token(db: Session, user: User, token_type: str, expires_minutes: int) -> str:
    raw = create_opaque_token()
    db.add(AuthToken(user_id=user.id, token_hash=hash_token(raw), token_type=token_type,
                     expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)))
    db.commit()
    return raw


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    return build_access_token(user), issue_database_token(db, user, "refresh", settings.REFRESH_TOKEN_EXPIRE_DAYS * 1440)


def consume_token(db: Session, raw_token: str, token_type: str, revoke: bool = True) -> AuthToken:
    record = db.query(AuthToken).filter(AuthToken.token_hash == hash_token(raw_token), AuthToken.token_type == token_type).first()
    now = datetime.now(timezone.utc)
    if not record or record.is_revoked:
        raise HTTPException(status_code=401 if token_type == "refresh" else 400, detail="Invalid or expired token")
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= now:
        record.is_revoked = True; db.commit()
        raise HTTPException(status_code=401 if token_type == "refresh" else 400, detail="Invalid or expired token")
    if revoke:
        record.is_revoked = True; db.commit()
    return record
