from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import InsufficientCreditsError
from app.models import User, Credit

settings = get_settings()

MODEL_COSTS = {
    "groq": settings.groq_credit_cost,
    "gemini": settings.gemini_credit_cost,
    "openai": settings.openai_credit_cost,
    "anthropic": settings.anthropic_credit_cost,
}


class CreditService:
    def get_balance(self, user: User, db: Session) -> Credit:
        credit = db.query(Credit).filter(Credit.user_id == user.id).first()
        if not credit:
            credit = Credit(user_id=user.id, balance=0.0)
            db.add(credit)
            db.commit()
            db.refresh(credit)
        return credit

    def ensure_credits(self, user: User, db: Session, model: str) -> float:
        cost = MODEL_COSTS.get(model, 5)
        credit = self.get_balance(user, db)
        if credit.balance < cost:
            raise InsufficientCreditsError(
                f"Credite insuficiente. Necesare: {cost}, disponibile: {credit.balance}"
            )
        return cost

    def deduct_credits(self, user: User, db: Session, cost: float) -> float:
        credit = self.get_balance(user, db)
        credit.balance -= cost
        db.commit()
        db.refresh(credit)
        return credit.balance

    def add_credits(self, user_id: int, db: Session, amount: float) -> float:
        credit = db.query(Credit).filter(Credit.user_id == user_id).first()
        if not credit:
            credit = Credit(user_id=user_id, balance=0.0)
            db.add(credit)
        credit.balance += amount
        db.commit()
        db.refresh(credit)
        return credit.balance


credit_service = CreditService()