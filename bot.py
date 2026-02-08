import logging
import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# 1. ПОЛУЧАЕМ КЛЮЧИ
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. НАСТРОЙКА GEMINI
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 3. ФУНКЦИЯ ДИАГНОСТИКИ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=user_chat_id, text="🕵️‍♂️ Начинаю диагностику сервера...")

    report = []
    
    # ПРОВЕРКА 1: Версия библиотеки
    try:
        lib_version = genai.__version__
        report.append(f"📚 Версия библиотеки Google: `{lib_version}`")
    except:
        report.append("📚 Версия библиотеки: Не определена (очень старая)")

    # ПРОВЕРКА 2: Какие модели видит ключ
    report.append("\n📋 **Список доступных моделей:**")
    try:
        found_any = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                report.append(f"- `{m.name}`")
                found_any = True
        
        if not found_any:
            report.append("❌ Список пуст! Ключ API верный, но модели недоступны (возможно, регион или настройки Google Cloud).")
    except Exception as e:
        report.append(f"💥 Ошибка при запросе списка: {e}")

    # ОТПРАВКА ОТЧЕТА
    final_text = "\n".join(report)
    await context.bot.send_message(chat_id=user_chat_id, text=final_text, parse_mode='Markdown')

# 4. ФАЛЬШИВЫЙ СЕРВЕР (Чтобы Render не падал)
from flask import Flask
import threading

app_server = Flask(__name__)
@app_server.route('/')
def index(): return "Diagnostic Bot Active"

def run_web():
    app_server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    if TELEGRAM_TOKEN:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.run_polling()