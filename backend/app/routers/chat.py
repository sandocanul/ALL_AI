import os
import re
import random
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from openai import OpenAI
import google.generativeai as genai
from groq import Groq

from app.database import get_db
from app.auth import get_current_active_user, get_current_user
from app.models import User, Credit, Message, ChatSession

SYSTEM_PROMPT = """Ești BIG AI, un asistent virtual extrem de inteligent, creativ și direct. 
Rolul tău este să oferi răspunsuri clare, bine formatate (folosind Markdown, liste, bold) și adaptate la contextul utilizatorului. 
Nu folosi introduceri lungi sau robotice. Fii un partener de brainstorming util, capabil să scrie cod, să planifice antrenamente, să dea idei de conținut sau să rezolve probleme logice."""

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    model: str = "groq"
    use_rag: bool = False
    session_id: Optional[int] = None
    is_quick_chat: bool = False
    history: Optional[List[Dict[str, Any]]] = []
    file_text: Optional[str] = None # <-- LINIA NOUĂ

class SessionRename(BaseModel):
    title: str


# --- RUTE PENTRU SESIUNI ---

@router.post("/sessions")
def create_chat_session(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    new_session = ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions")
def get_chat_sessions(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.timestamp.desc()).all()
    return sessions

@router.get("/session/{session_id}")
def get_session_history(session_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.user_id == current_user.id, Message.session_id == session_id).order_by(Message.id.asc()).all()
    return messages

@router.put("/sessions/{session_id}")
def rename_session(session_id: int, data: SessionRename, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesiunea nu a fost găsită")
    
    session.title = data.title
    db.commit()
    return {"status": "success", "new_title": data.title}

@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesiunea nu a fost găsită")
    
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"status": "success", "message": "Sesiune ștearsă"}

@router.get("/credits")
def get_user_credits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    credits = db.query(Credit).filter(Credit.user_id == current_user.id).first()
    balance = credits.balance if credits else 1000 
    return {"balance": balance}


# --- RUTA PRINCIPALĂ DE CHAT ---

@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_credits = db.query(Credit).filter(Credit.user_id == current_user.id).first()
    if not user_credits or user_credits.balance < 1:
        raise HTTPException(status_code=402, detail="Nu ai suficiente credite!")

    reply = ""
    session_id_to_use = request.session_id
    user_text = request.message.strip()

    try:
       # 1. VERIFICĂM DACĂ ESTE COMANDĂ DE GENERARE IMAGINE
        if user_text.lower().startswith("/image"):
            raw_prompt = user_text[6:].strip()
            
            if not raw_prompt:
                reply = "Te rog să scrii ce vrei să generez. Exemplu: `/image un thumbnail cu un peisaj cibernetic`"
            else:
                # --- MAGIA NOUĂ: AI-ul TRADUCE ȘI OPTIMIZEAZĂ PROMPTUL ---
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                instruction = (
                    "Translate the following image generation prompt to English and enhance it to be "
                    "highly detailed, cinematic, and photorealistic for an AI image generator (like Flux/Midjourney). "
                    "Return ONLY the English prompt, absolutely no introductory text, no quotes, no explanations.\n\n"
                    f"User prompt: {raw_prompt}"
                )
                
                enhancement_response = client.chat.completions.create(
                    model="qwen/qwen3.6-27b", # Folosim modelul rapid pentru asta
                    messages=[{"role": "user", "content": instruction}]
                )
                
                # Curățăm rezultatul (scoatem <think> dacă există)
                enhanced_prompt_english = enhancement_response.choices[0].message.content.strip()
                enhanced_prompt_english = re.sub(r'<think>.*?</think>', '', enhanced_prompt_english, flags=re.DOTALL).strip()
                
                # --- GENERĂM IMAGINEA CU PROMPTUL SUPER-OPTIMIZAT ---
                encoded_prompt = urllib.parse.quote(enhanced_prompt_english)
                seed = random.randint(1, 1000000)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&nologo=true&seed={seed}"
                
                # Returnăm imaginea + afișăm și promptul în engleză ca să vezi ce a generat!
                reply = f"Iată conceptul vizual:\n\n![Thumbnail Generat]({image_url})\n\n*🪄 Prompt optimizat:* `{enhanced_prompt_english}`"
        
        # 2. DACĂ NU E IMAGINE, FOLOSIM INTELIGENȚA ARTIFICIALĂ
        # 2. DACĂ NU E IMAGINE, FOLOSIM INTELIGENȚA ARTIFICIALĂ
        else:
            messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
            if request.history:
                for past_message in request.history:
                    if past_message.get("content") != request.message:
                        messages_for_ai.append(past_message)
            
            # --- MAGIA NOUĂ PENTRU FIȘIERE ---
            # Dacă am primit un fișier, îl combinăm cu mesajul tău pe ascuns
            final_prompt = request.message
            if request.file_text:
                final_prompt = f"Ai primit următorul document atașat:\n\n{request.file_text}\n\nÎntrebarea utilizatorului: {request.message}"

            messages_for_ai.append({"role": "user", "content": final_prompt})

            if request.model == "groq":
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                response = client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=messages_for_ai
                )
                reply = response.choices[0].message.content

            elif request.model == "gemini":
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                model = genai.GenerativeModel('gemini-3.5-flash', system_instruction=SYSTEM_PROMPT)
                
                gemini_history = []
                if request.history:
                     for msg in request.history:
                         role = "model" if msg["role"] == "assistant" else "user"
                         if msg.get("content") != request.message:
                            gemini_history.append({"role": role, "parts": [msg["content"]]})
                
                chat_session = model.start_chat(history=gemini_history)
                # Trimitem final_prompt-ul cu tot cu fișier la Gemini
                response = chat_session.send_message(final_prompt)
                reply = response.text

            elif request.model == "llama":
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPEN_ROUTER_KEY"))
                response = client.chat.completions.create(
                    model="inclusionai/ling-3.0-flash-fin:free",
                    messages=messages_for_ai
                )
                reply = response.choices[0].message.content
                
            else:
                raise HTTPException(status_code=400, detail="Model necunoscut!")

            # Curățăm gândurile modelelor
            reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()

        # --- SALVARE ÎN BAZA DE DATE ---
        user_credits.balance -= 1

        if not request.is_quick_chat:
            if not session_id_to_use:
                titlu = request.message[:30] + ("..." if len(request.message) > 30 else "")
                noua_sesiune = ChatSession(user_id=current_user.id, title=titlu)
                db.add(noua_sesiune)
                db.commit()
                db.refresh(noua_sesiune)
                session_id_to_use = noua_sesiune.id
            
            user_msg_db = Message(user_id=current_user.id, session_id=session_id_to_use, sender="user", content=request.message)
            ai_msg_db = Message(user_id=current_user.id, session_id=session_id_to_use, sender="ai", content=reply)
            
            db.add(user_msg_db)
            db.add(ai_msg_db)
            db.commit()

        return {
            "response": reply,
            "remaining_credits": user_credits.balance,
            "session_id": session_id_to_use
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare procesare chat: {str(e)}")