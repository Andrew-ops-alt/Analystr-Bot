import logging
import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- ПОЛУЧАЕМ КЛЮЧИ ИЗ НАСТРОЕК СЕРВЕРА ---
# (На сервере мы их пропишем в специальном меню)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Настройка Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Используем проверенную модель
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("ОШИБКА: Ключ Google не найден!")

# --- ИНСТРУКЦИЯ КАППЕРА (СИСТЕМНЫЙ ПРОМПТ) ---
SYSTEM_PROMPT = """
ТЫ — ПРОФЕССИОНАЛЬНЫЙ СПОРТИВНЫЙ АНАЛИТИК (BETTING EXPERT).
Твоя цель: Дать максимально точный прогноз, чтобы пользователь выиграл ставку.

ТВОЙ АЛГОРИТМ:
1.  🌍 Определи вид спорта и важность матча (Лига Чемпионов, NBA, проходной матч).
2.  📊 Вспомни стили команд (Атакующий, Автобус, Контратакующий).
3.  ⚔️ Вспомни историю личных встреч (кто для кого "неудобный соперник").
4.  🧠 Сделай вывод, исходя из мотивации (кому победа нужнее).

ФОРМАТ ОТВЕТА:
🏆 **Матч:** [Команды]
📊 **Анализ:** [3-4 предложения про тактику и форму]
💣 **Рискованная ставка:** [Высокий кэф] (Обоснование)
✅ **Надежная ставка:** [Низкий кэф] (Обоснование)
🔮 **Точный счет (предположение):** [Счет]
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Я AI-Каппер.** Я работаю 24/7.\n\n"
        "Напиши мне название матча (например: `Реал - Барселона`) или скопируй новости о составах.\n"
        "Я проанализирую данные и дам прогноз."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return

    # Сообщение о том, что бот думает
    status_msg = await update.message.reply_text("⏳ *Изучаю статистику матча...*", parse_mode='Markdown')
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Собираем запрос
        full_query = f"{SYSTEM_PROMPT}\n\nЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_text}"
        
        response = model.generate_content(full_query)
        
        # Удаляем сообщение "Изучаю..." и пишем ответ
        await status_msg.delete()
        await update.message.reply_text(response.text, parse_mode='Markdown')
        
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Ошибка анализа: {e}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("ОШИБКА: Токен Telegram не найден в переменных окружения!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Бот-Каппер запущен на сервере!")
        app.run_polling()