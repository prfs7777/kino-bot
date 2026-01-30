import os
import sqlite3
import logging
import telebot
import time
from flask import Flask
from threading import Thread

# 1. LOGGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. RENDER PORTINI ALDASH (ENG SODDA VARIANT)
app = Flask('')

@app.route('/')
def home():
    return "Bot is active", 200

def run_flask():
    # Render avtomat PORT beradi
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Flaskni alohida thread'da yurgizamiz
Thread(target=run_flask, daemon=True).start()

# 3. BOT SOZLAMALARI
TOKEN = '7011547936:AAHFfUyzTg9EUhnq6KrKEP69pOm_uTHn-7Q'
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
ADMIN_LOGIN = "azik1202"
active_admins = set()

# 4. DATABASE
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT PRIMARY KEY, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# 5. ADMIN FUNKSIYALARI
@bot.message_handler(commands=['admin'])
def ask_login(message):
    bot.send_message(message.chat.id, "🔐 Login:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        active_admins.add(message.from_user.id)
        bot.reply_to(message, "✅ Tasdiqlandi!")
    else:
        bot.reply_to(message, "❌ Xato!")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in active_admins: return
    if message.reply_to_message and message.reply_to_message.video:
        msg = bot.reply_to(message, "Format: `ID Nomi`")
        bot.register_next_step_handler(msg, process_add, message.reply_to_message.video.file_id)

def process_add(message, file_id):
    try:
        p = message.text.split(maxsplit=1)
        db.execute("INSERT OR REPLACE INTO movies VALUES (?,?,?)", (p[0], p[1], file_id))
        db.commit()
        bot.send_message(message.chat.id, f"✅ Qo'shildi: {p[1]}")
    except:
        bot.send_message(message.chat.id, "❌ Xato!")

@bot.message_handler(commands=['remove'])
def remove(message):
    if message.from_user.id not in active_admins: return
    p = message.text.split()
    if len(p) > 1:
        db.execute("DELETE FROM movies WHERE m_id=?", (p[1],))
        db.commit()
        bot.reply_to(message, "✅ O'chirildi.")

# 6. QIDIRUV VA RO'YXAT
@bot.message_handler(commands=['start'])
def start(m):
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("🎬 Ro'yxat", callback_data="list"))
    bot.send_message(m.chat.id, "Kino kodini yuboring:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "list")
def list_m(call):
    rows = db.execute("SELECT m_id, m_name FROM movies").fetchall()
    text = "🎬 **Kinolar:**\n\n" + "\n".join([f"`{r[0]}` - {r[1]}" for r in rows]) if rows else "Bo'sh."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def find(message):
    q = message.text
    res = db.execute("SELECT f_id, m_name FROM movies WHERE m_id=? OR m_name LIKE ?", (q, f'%{q}%')).fetchone()
    if res: bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else: bot.send_message(message.chat.id, "🔍 Topilmadi.")

# 7. BARQAROR ISHLATISH (AVTOMAT QAYTA YONISH)
while True:
    try:
        logger.info("Bot ishga tushdi...")
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        time.sleep(10) # Aloqa uzilsa 10 soniya kutib qayta ulanadi
