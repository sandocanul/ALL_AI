# AI Platform — Memorie Comuna Multi-Model

## 🚀 Caracteristici
- **Multi-AI**: Groq, Gemini, OpenAI, Anthropic — aceeasi memorie RAG
- **Credite per utilizare**: costuri diferite per model
- **RAG local**: ChromaDB (dev) / Qdrant (prod)
- **Plati**: Stripe Checkout + Webhook
- **Frontend**: Chat web modern
- **Telegram Bot**: Comenzi /login, /cont, /register

## ⚡ Pornire rapida (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# Editeaza .env cu cheile tale API
uvicorn app.main:app --reload"# ALL_AI" 
