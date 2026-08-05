import stripe
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Credit, Payment
load_dotenv()
# Setăm cheia secretă de TEST de la Stripe (nu încasa bani reali pe ea)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/api/payments", tags=["Payments"])

class PaymentVerify(BaseModel):
    session_id: str

@router.post("/create-checkout-session")
def create_checkout_session(current_user: User = Depends(get_current_active_user)):
    try:
        # 1. Verificăm în terminal dacă s-a încărcat cheia
        print("🔍 CHEIE STRIPE DETECTATĂ:", stripe.api_key[:12] if stripe.api_key else "❌ NICIUNA (None)")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Pachet 100 Credite AI',
                        'description': 'Valabil pentru modelele Groq și Gemini.',
                    },
                    'unit_amount': 500, # 5.00 USD
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://127.0.0.1:5500/BIG_AI/frontend/index.html?payment=success&session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://127.0.0.1:5500/BIG_AI/frontend/index.html?payment=canceled',
            client_reference_id=str(current_user.id)
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        # 2. Printăm eroarea exactă în terminalul VS Code!
        print(f"❌ EROARE EXACTĂ STRIPE: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
def verify_payment(data: PaymentVerify, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        # Întrebăm Stripe dacă sesiunea chiar a fost plătită
        session = stripe.checkout.Session.retrieve(data.session_id)
        
        if session.payment_status == "paid":
            # Căutăm dacă nu cumva am procesat deja această sesiune Stripe
            existing_payment = db.query(Payment).filter(Payment.user_id == current_user.id, Payment.status == session.id).first()
            
            if not existing_payment:
                # 1. Adăugăm plata în istoricul bazei de date (salvăm ID-ul Stripe în status ca să nu mai crape)
                new_payment = Payment(
                    user_id=current_user.id, 
                    amount=session.amount_total, 
                    status=session.id
                )
                db.add(new_payment)
                
                # 2. Adăugăm cele 100 de credite utilizatorului
                user_credits = db.query(Credit).filter(Credit.user_id == current_user.id).first()
                if user_credits:
                    user_credits.balance += 100
                else:
                    new_credit = Credit(user_id=current_user.id, balance=100)
                    db.add(new_credit)
                
                db.commit()
                print("✅ CREDITE ADĂUGATE CU SUCCES ÎN BAZA DE DATE!")
                return {"status": "success", "message": "Credite adăugate cu succes!"}
            
            return {"status": "already_processed", "message": "Plata a fost deja procesată."}
        
        return {"status": "unpaid", "message": "Plata nu a fost finalizată."}
    except Exception as e:
        db.rollback()
        print(f"❌ EROARE EXACTĂ LA VERIFY: {e}")  # Vedem exact problema în terminal!
        raise HTTPException(status_code=500, detail=str(e))