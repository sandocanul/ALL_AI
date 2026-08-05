"""Entrypoint FastAPI"""
from dotenv import load_dotenv
load_dotenv()  # Asta forțează citirea fișierului .env instant!
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import credits
from app.database import Base, init_db, engine, Base
from app.routers import auth, chat, payments
from fastapi.responses import RedirectResponse
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="AI Platform",
    description="Platforma AI cu memorie comuna, credite si rutare multi-model",
    version="1.0.0"
)
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
# CORS pentru frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, # <--- AICI AM MODIFICAT
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initializare DB la startup
@app.on_event("startup")
def on_startup():
    init_db()

# Includere rute
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(credits.router)
app.include_router(payments.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-platform"}