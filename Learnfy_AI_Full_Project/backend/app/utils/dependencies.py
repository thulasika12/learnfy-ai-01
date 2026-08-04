"""
Reusable FastAPI dependencies: get_current_user and role-based guards.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.security import decode_access_token
from app.models.user import User, UserRole
from app.models.teacher_verification import TeacherVerification, VerificationStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
optional_bearer = HTTPBearer(auto_error=False)


def _resolve_user(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return db.query(User).filter(User.id == int(user_id)).first()
    except (TypeError, ValueError):
        return None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = _resolve_user(token, db)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the signed-in user when a valid bearer token is supplied."""
    if credentials is None:
        return None
    user = _resolve_user(credentials.credentials, db)
    if user is None or not user.is_active:
        return None
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory to restrict an endpoint to specific roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


require_admin = require_role(UserRole.admin)
def require_teacher(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    if current_user.role == UserRole.admin:
        return current_user
    approved = db.query(TeacherVerification.id).filter(
        TeacherVerification.user_id == current_user.id,
        TeacherVerification.status == VerificationStatus.approved,
    ).first()
    if current_user.role != UserRole.teacher or not current_user.is_verified_teacher or not approved:
        raise HTTPException(status_code=403, detail="Approved teacher verification is required")
    return current_user
