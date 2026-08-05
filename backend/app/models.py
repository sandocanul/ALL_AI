from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)  # <-- Adaugă această linie!
    hashed_password = Column(String)

class Credit(Base):
    __tablename__ = "credits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Integer, default=100)

# TABEL NOU: Sesiunile de Chat (conversatiile din Sidebar)
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="Conversație nouă")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# TABEL ACTUALIZAT: Mesajele
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))  # Legătura cu sesiunea
    sender = Column(String)  
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # TABEL RESTAURAT: Plățile (Stripe)
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    status = Column(String, default="pending")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())