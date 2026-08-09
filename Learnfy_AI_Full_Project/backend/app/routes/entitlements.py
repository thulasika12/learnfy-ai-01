from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.services.entitlement_service import snapshot
from app.utils.dependencies import get_current_user
router = APIRouter(prefix="/entitlements", tags=["Entitlements"])
@router.get("/me")
def my_entitlements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return snapshot(db, user.id)
