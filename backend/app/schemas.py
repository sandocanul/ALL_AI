from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = ""
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str
    model: str = "groq"
    use_rag: bool = True


class ChatResponse(BaseModel):
    response: str
    model_used: str
    credits_deducted: float
    remaining_credits: float
    sources: Optional[List[str]] = None


class CreditOut(BaseModel):
    balance: float

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    checkout_url: str
    session_id: str