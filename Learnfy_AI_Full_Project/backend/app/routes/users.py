"""User profile, avatar and account routes."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserOut, UserUpdate, DeleteAccountRequest
from app.services.file_service import save_upload_file
from app.config.security import verify_password
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    db.commit(); db.refresh(current_user)
    return current_user

@router.post("/profile/avatar", response_model=UserOut)
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.profile_image = save_upload_file(file, category="profile", allowed_extensions={".jpg", ".jpeg", ".png", ".webp"})
    db.commit(); db.refresh(current_user)
    return current_user

@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_account(payload: DeleteAccountRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.password, current_user.password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    db.delete(current_user); db.commit()
    return {"message": "Account deleted successfully"}
