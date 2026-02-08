import logging
import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- 1. КЛЮЧИ ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# --- 2. НАСТРОЙКИ ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- СПИСОК МОДЕЛЕЙ (ОТ ЛУЧШЕЙ К ПРОСТОЙ) ---
# Бот будет пробовать их по очереди, пока одна не сработает
MODEL_LIST = [
    "gemini-1.5-flash",          # Самая быстрая и новая
    "gemini-1.5-flash-001",      # Стабильная версия
    "gemini-1.5-flash-8b",       # Облегченная версия
    "gemini-1.0-pro",            # Классика (работает всегда)
    "gemini-pro"                 # Старое название
]

# --- 3. ИНСТРУКЦИЯ (ПРОМПТ) ---
SYSTEM_PROMPT = """
ТЫ — СПОРТИВНЫЙ АНАЛИТИК.
Твоя задача: Дать краткий, четкий прогноз на матч.
Формат:
1. 📊 Анализ формы.
2. 🏆 Кто победит, поясняя свое решение.
3. 💣 Ставки.
"""

# --- 4. ФУНКЦИИ БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥊 Я готов! Пиши матч, я переберу все нейросети, чтобы ответить.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return

    status_msg = await update.message.reply_text("⏳ Подбираю рабочую модель...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # --- МАГИЯ: ПЕРЕБОР МОДЕЛЕЙ ---
    final_response = None
    last_error = ""

    # Пробуем каждую модель из списка по очереди
    for model_name in MODEL_LIST:
        try:
            # Пытаемся подключиться к конкретной модели
            model = genai.GenerativeModel(model_name)
            query = f"{SYSTEM_PROMPT}\n\nЗАПРОС: {user_text}"
            
            # Если сработает - отлично, выходим из цикла
            response = model.generate_content(query)
            final_response = f"🤖 *Ответила модель: {model_name}*\n\n" + response.text
            break 
        except Exception as e:
            # Если ошибка - запоминаем её и идем к следующей модели
            print(f"Модель {model_name} не сработала: {e}")
            last_error = str(e)
            continue

    # Отправляем результат
    try:
        await status_msg.delete()
        if final_response:
            await update.message.reply_text(final_response, parse_mode='Markdown')
        else:
            # Если перепробовали ВСЁ и ничего не вышло
            await update.message.reply_text(f"❌ Не удалось найти рабочую модель. Последняя ошибка: {last_error}")
    except Exception:
        pass

# --- 5. ФАЛЬШИВЫЙ СЕРВЕР ДЛЯ RENDER ---
app_server = Flask(__name__)

@app_server.route('/')
def index():
    return "Bot is working hard!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app_server.run(host="0.0.0.0", port=port)

# --- 6. ЗАПУСК ---
if __name__ == '__main__':
    server_thread = threading.Thread(target=run_web_server)
    server_thread.start()

    if TELEGRAM_TOKEN:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        print("Бот-Вездеход запущен!")
        app.run_polling()