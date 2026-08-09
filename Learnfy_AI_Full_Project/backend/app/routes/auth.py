"""Complete authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.security import hash_password, verify_password
from app.config.settings import settings
from app.models.user import User
from app.schemas.user_schema import (UserRegister, UserLogin, Token, UserOut, ForgotPasswordRequest,
    ResetPasswordRequest, RefreshTokenRequest, ChangePasswordRequest)
from app.services.auth_service import (register_user, authenticate_user, issue_token_pair,
    issue_database_token, consume_token, build_access_token)
from app.services.email_service import send_password_reset_email
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
