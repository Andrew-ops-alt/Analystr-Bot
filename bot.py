import logging
import os
import threading
from flask import Flask # <-- Новая библиотека для "обманки"
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# --- НАСТРОЙКА GEMINI ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

# --- ИНСТРУКЦИЯ КАППЕРА ---
SYSTEM_PROMPT = """
ТЫ — ПРОФЕССИОНАЛЬНЫЙ СПОРТИВНЫЙ АНАЛИТИК.
Твоя задача: Дать прогноз на матч.
Формат:
1. Анализ формы команд.
2. Ставка (Риск / Надежная).
3. Точный счет.
4. Статистика последних 5 матчей.
"""

# --- ФУНКЦИИ БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ Привет! Я AI-Каппер. Напиши, какой матч разобрать.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return
    status = await update.message.reply_text("⏳ Анализирую матч...")
    try:
        query = f"{SYSTEM_PROMPT}\n\nМатч: {user_text}"
        response = model.generate_content(query)
        await status.delete()
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await status.edit_text(f"Ошибка: {e}")

# ==========================================
# 👇 ВОТ ЭТА ЧАСТЬ - "ОБМАНКА" ДЛЯ RENDER 👇
# ==========================================
app_server = Flask(__name__)

@app_server.route('/')
def index():
    return "Бот работает! (Это заглушка для Render)"

def run_web_server():
    # Render требует слушать порт, который он выдаст, или 10000
    port = int(os.environ.get("PORT", 10000))
    app_server.run(host="0.0.0.0", port=port)
# ==========================================


if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("ОШИБКА: Нет токена!")
    else:
        # 1. Запускаем "фальшивый сайт" в фоновом режиме
        server_thread = threading.Thread(target=run_web_server)
        server_thread.start()

        # 2. Запускаем основного бота
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Бот и веб-сервер запущены!")
        app.run_polling()