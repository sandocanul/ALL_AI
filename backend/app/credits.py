"""Endpoint credite: sold, istoric"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_active_user
from app.schemas import CreditOut
from app.services.credit_service import credit_service

router = APIRouter(prefix="/api/credits", tags=["Credite"])


@router.get("/balance", response_model=CreditOut)
def get_balance(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    credit = credit_service.get_balance(current_user, db)
    # Returnam obiect partial
    from BIG_AI.backend.app.models import Credit
    c = db.query(Credit).filter(Credit.user_id == current_user.id).first()
    return c 