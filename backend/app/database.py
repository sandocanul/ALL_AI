import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Luăm link-ul bazei de date din setările Render. Dacă nu există, folosim SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# 2. Reparăm o mică problemă tehnică pe care o au unele platforme cu numele link-ului
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Creăm conexiunea (SQLite are nevoie de o setare specială, Postgres nu)
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Funcția de care au nevoie routerele pentru a vorbi cu baza de date
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Funcția care creează tabelele în baza de date la pornirea aplicației
def init_db():
    Base.metadata.create_all(bind=engine)