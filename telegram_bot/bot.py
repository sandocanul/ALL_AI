"""Bot Telegram pentru AI Platform"""
import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

API_BASE = os.getenv("API_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stocare temporara tokeni (in productie foloseste Redis/DB)
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bun venit la AI Platform!\\n"
        "Foloseste /login EMAIL PAROLA\\n"
        "Sau /register EMAIL PAROLA [NUME]"
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Utilizare: /register EMAIL PAROLA [NUME]")
        return
    email, password = context.args[0], context.args[1]
    full_name = context.args[2] if len(context.args) > 2 else ""
    
    try:
        r = requests.post(f"{API_BASE}/api/auth/register", json={
            "email": email, "password": password, "full_name": full_name
        })
        data = r.json()
        user_sessions[update.effective_user.id] = data["access_token"]
        await update.message.reply_text("✅ Inregistrat! Ai primit 1000 credite.")
    except Exception as e:
        await update.message.reply_text(f"❌ Eroare: {e}")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Utilizare: /login EMAIL PAROLA")
        return
    try:
        r = requests.post(f"{API_BASE}/api/auth/login", json={
            "email": context.args[0], "password": context.args[1]
        })
        data = r.json()
        user_sessions[update.effective_user.id] = data["access_token"]
        await update.message.reply_text("✅ Logat cu succes!")
    except Exception as e:
        await update.message.reply_text(f"❌ Eroare: {e}")


async def cont(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    token = user_sessions.get(uid)
    if not token:
        await update.message.reply_text("❌ Nu esti logat. Foloseste /login")
        return
    
    try:
        r = requests.get(f"{API_BASE}/api/credits/balance", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        keyboard = [
            [InlineKeyboardButton("Groq (1c)", callback_data="model:groq")],
            [InlineKeyboardButton("Gemini (5c)", callback_data="model:gemini")],
            [InlineKeyboardButton("OpenAI (10c)", callback_data="model:openai")],
        ]
        await update.message.reply_text(
            f"💰 Sold: {data['balance']} credite\\nAlege modelul:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(f"Eroare: {e}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("model:"):
        model = data.split(":")[1]
        context.user_data["model"] = model
        await query.edit_message_text(f"✅ Model setat: {model.upper()}")


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    token = user_sessions.get(uid)
    if not token:
        await update.message.reply_text("❌ Logheaza-te mai intai cu /login")
        return
    
    model = context.user_data.get("model", "groq")
    try:
        r = requests.post(f"{API_BASE}/api/chat/", headers={"Authorization": f"Bearer {token}"}, json={
            "message": update.message.text,
            "model": model,
            "use_rag": True
        })
        data = r.json()
        await update.message.reply_text(
            f"{data['response']}\\n\\n— Model: {data['model_used']} | Cost: {data['credits_deducted']} credite | Ramas: {data['remaining_credits']}"
        )
    except Exception as e:
        await update.message.reply_text(f"Eroare: {e}")


def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("cont", cont))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    logger.info("Bot pornit...")
    app.run_polling()


if __name__ == "__main__":
    main()