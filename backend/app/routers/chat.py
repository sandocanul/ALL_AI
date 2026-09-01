import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from openai import OpenAI
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Credit, Message, ChatSession
from app.auth import get_current_user
from groq import Groq
import google.generativeai as genai
# Asta va ghida comportamentul AI-ului pentru toți utilizatorii
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
    history: Optional[List[Dict[str, Any]]] = [] # NOU: Primim o listă de dicționare din frontend

# 2. RUTA NOUĂ: Creează o sesiune nouă de chat
@router.post("/sessions")
def create_chat_session(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    new_session = ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

# 3. RUTA NOUĂ: Aduce lista cu toate sesiunile pentru Sidebar
@router.get("/sessions")
def get_chat_sessions(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.timestamp.desc()).all()
    return sessions

# 4. RUTA ACTUALIZATĂ: Trimite mesaj și procesează Quick Chat
@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_credits = db.query(Credit).filter(Credit.user_id == current_user.id).first()
    if not user_credits or user_credits.balance < 1:
        raise HTTPException(status_code=402, detail="Nu ai suficiente credite!")

    reply = ""
    try:
        # Așa "lipim" totul logic pentru AI:
        # 1. System Prompt-ul
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 2. Toată lista cu istoricul pe care am primit-o din frontend (ultimele 10 mesaje)
        if request.history:
            for past_message in request.history:
                # Ne asigurăm că adăugăm doar mesajele vechi (fără cel proaspăt, ca să nu-l dublăm)
                if past_message.get("content") != request.message:
                    messages_for_ai.append(past_message)
        
        # 3. Mesajul nou de la utilizator
        messages_for_ai.append({"role": "user", "content": request.message})

        if request.model == "groq":
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=messages_for_ai # În loc de lista manuală, punem lista construită mai sus!
            )
            reply = response.choices[0].message.content
            
        elif request.model == "gemini":
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(
                'gemini-3.5-flash',
                system_instruction=SYSTEM_PROMPT
            )
            # La Gemini trebuie să-i convertim lista în formatul lui
            gemini_history = []
            if request.history:
                 for msg in request.history:
                     # Gemini folosește "model" în loc de "assistant" și "user"
                     role = "model" if msg["role"] == "assistant" else "user"
                     if msg.get("content") != request.message:
                        gemini_history.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(request.message)
            reply = response.text

        elif request.model == "llama":
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPEN_ROUTER_KEY"),
            )
            response = client.chat.completions.create(
                model="inclusionai/ling-3.0-flash-fin:free",
                messages=messages_for_ai # La fel ca la Groq
            )
            reply = response.choices[0].message.content
           
            
        else:
         raise HTTPException(status_code=400, detail="Model necunoscut!")
            # --- PARTEA NOUĂ DE SALVARE ÎN BAZA DE DATE ---
        session_id_to_use = request.session_id
 # --- LINIA NOUĂ DE CURĂȚARE ---
        # Ștergem tag-urile <think> și tot ce e în interiorul lor
        reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
        
        # (Urmează codul pe care l-am făcut mai devreme cu salvarea în DB)
        session_id_to_use = request.session_id
        # Dacă NU e Quick Chat, salvăm în baza de date
        if not request.is_quick_chat:
            if not session_id_to_use:
                # 1. Dacă nu avem o sesiune, creăm una nouă
                # Titlul va fi primele 30 de litere din mesajul tău
                titlu_sesiune = request.message[:30] + "..." if len(request.message) > 30 else request.message
                new_session = ChatSession(user_id=current_user.id, title=titlu_sesiune)
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                session_id_to_use = new_session.id
            
            # 2. Salvăm mesajul tău
            user_msg = Message(user_id=current_user.id, session_id=session_id_to_use, sender="user", content=request.message)
            db.add(user_msg)
            
            # 3. Salvăm răspunsul AI-ului
            ai_msg = Message(user_id=current_user.id, session_id=session_id_to_use, sender="ai", content=reply)
            db.add(ai_msg)
            
            db.commit()
            
        # Returnăm răspunsul, dar trimitem și ID-ul sesiunii înapoi la Frontend
        return {
            "response": reply, 
            "remaining_credits": 999, # Sau cum ai tu logica de credite aici
            "session_id": session_id_to_use # IMPORTANT: Frontend-ul are nevoie de el!
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare AI: {str(e)}")
    user_credits.balance -= 1
    # SALVĂM DOAR DACĂ NU ESTE QUICK CHAT
    session_id_to_use = request.session_id

    if not request.is_quick_chat:
            # 1. Dacă nu avem sesiune (e primul mesaj după ce ai apăsat + Chat Nou)
            if not session_id_to_use:
                # Creăm titlul direct din mesaj. Punem "..." DOAR dacă depășește 30 de litere
                titlu = request.message[:30] + ("..." if len(request.message) > 30 else "")
                
                noua_sesiune = ChatSession(user_id=current_user.id, title=titlu)
                db.add(noua_sesiune)
                db.commit()
                db.refresh(noua_sesiune)
                session_id_to_use = noua_sesiune.id
            
            # 2. Acum salvăm mesajele sub ID-ul corect (fie cel nou, fie cel vechi)
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

# 5. RUTA ACTUALIZATĂ: Aduce istoricul DOAR pentru o anumită sesiune
@router.get("/history/{session_id}")
def get_session_history(session_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.user_id == current_user.id, Message.session_id == session_id).order_by(Message.timestamp.asc()).all()
    return messages
@router.get("/credits")
def get_user_credits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    credits = db.query(Credit).filter(Credit.user_id == current_user.id).first()
    # Dacă e nou, îi dăm 1000 default vizual (sau cât vrei tu)
    balance = credits.balance if credits else 1000 
    return {"balance": balance}
from pydantic import BaseModel

# Schema pentru primirea noului titlu
class SessionRename(BaseModel):
    title: str

@router.put("/sessions/{session_id}")
def rename_session(session_id: int, data: SessionRename, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Căutăm sesiunea
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesiunea nu a fost găsită")
    
    # Modificăm titlul
    session.title = data.title
    db.commit()
    return {"status": "success", "new_title": data.title}

@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Căutăm sesiunea
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesiunea nu a fost găsită")
    
    # Ștergem întâi mesajele asociate cu sesiunea ca să nu lăsăm date "orfane" în baza de date
    db.query(Message).filter(Message.session_id == session_id).delete()
    
    # Apoi ștergem sesiunea însăși
    db.delete(session)
    db.commit()
    return {"status": "success", "message": "Sesiune ștearsă"}
# --- RUTE NOI PENTRU SALVAREA ȘI ÎNCĂRCAREA ISTORICULUI ---

@router.get("/sessions")
async def get_sessions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Aducem toate conversațiile utilizatorului, ordonate de la cea mai nouă
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.timestamp.desc()).all()
    return sessions

@router.get("/session/{session_id}")
async def get_session_history(session_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Aducem toate mesajele dintr-o conversație anume
    messages = db.query(Message).filter(
        Message.session_id == session_id, 
        Message.user_id == current_user.id
    ).order_by(Message.id.asc()).all()
    return messages