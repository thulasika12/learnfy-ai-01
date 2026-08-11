"""Complete authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.security import hash_password, verify_password
from app.config.settings import settings
from app.models.user import User
from app.schemas.user_schema import (UserRegister, UserLogin, Token, UserOut, ForgotPasswordRequest,
    ResetPasswordRequest, RefreshTokenRequest, ChangePasswordRequest, EmailVerificationRequest)
from app.services.auth_service import (register_user, authenticate_user, issue_token_pair,
    issue_database_token, consume_token, build_access_token)
from app.services.email_service import send_password_reset_email, send_email_verification_code
from app.models.email_verification import EmailVerificationCode
from app.config.security import create_opaque_token, hash_token
from datetime import datetime, timedelta, timezone
import secrets
from app.utils.dependencies import get_current_user
from app.services.rate_limit import enforce

router = APIRouter(prefix="/auth", tags=["Authentication"])
def token_response(db: Session, user: User) -> Token:
    access, refresh = issue_token_pair(db, user)
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/register", status_code=201)
def register(payload: UserRegister, request: Request, db: Session = Depends(get_db)):
    enforce(request, "register", 5, 3600)
    register_user(db, payload)
    return {"message": "Account created successfully. You can now log in."}


def issue_email_code(db: Session, user: User) -> None:
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.query(EmailVerificationCode).filter(EmailVerificationCode.user_id == user.id, EmailVerificationCode.is_used.is_(False)).update({EmailVerificationCode.is_used: True}, synchronize_session=False)
    db.add(EmailVerificationCode(user_id=user.id, code_hash=hash_token(code), expires_at=datetime.now(timezone.utc)+timedelta(minutes=15)))
    db.commit(); send_email_verification_code(user.email, code)


@router.post("/email-verification/request")
def request_email_verification(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.is_email_verified: return {"message": "Email is already verified"}
    enforce(request, f"verify_email:{user.id}", 5, 3600); issue_email_code(db, user)
    return {"message": "Verification code sent"}


@router.post("/email-verification/verify", response_model=Token)
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(EmailVerificationCode).filter(EmailVerificationCode.user_id == user.id, EmailVerificationCode.is_used.is_(False)).order_by(EmailVerificationCode.created_at.desc()).first()
    if not record or record.attempts >= 5: raise HTTPException(400, "Invalid or expired verification code")
    expires = record.expires_at.replace(tzinfo=timezone.utc) if record.expires_at.tzinfo is None else record.expires_at
    record.attempts += 1
    if expires <= datetime.now(timezone.utc) or record.code_hash != hash_token(payload.code):
        db.commit(); raise HTTPException(400, "Invalid or expired verification code")
    record.is_used = True; user.is_email_verified = True; db.commit(); db.refresh(user)
    return token_response(db, user)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    enforce(request, "login", 10, 900)
    return token_response(db, authenticate_user(db, payload))


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    old = consume_token(db, payload.refresh_token, "refresh", revoke=True)
    user = db.query(User).filter(User.id == old.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User is unavailable")
    return token_response(db, user)


@router.post("/logout")
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    consume_token(db, payload.refresh_token, "refresh", revoke=True)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    enforce(request, "forgot_password", 5, 3600)
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    message = "If that email exists, a reset link has been sent."
    if user and user.is_active:
        token = issue_database_token(db, user, "password_reset", settings.PASSWORD_RESET_EXPIRE_MINUTES)
        send_password_reset_email(user.email, token)
    return {"message": message}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    enforce(request, "reset_password", 10, 3600)
    record = consume_token(db, payload.reset_token, "password_reset", revoke=True)
    user = db.query(User).filter(User.id == record.user_id, User.email == str(payload.email).lower()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset request")
    user.password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
