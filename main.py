import os
import sqlite3
import logging
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# 1. LOGGING (Xatolarni Render panelida ko'rish uchun)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. RENDER UCHUN FLASK SERVER
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!", 200

def run_flask():
    # Render loglariga ko'ra port 10000 ishlatilyapti
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# 3. BOTNI "UXLAB" QOLISHIDAN SAQLASH (Auto-ping)
def keep_alive():
    # Bot o'z manziliga har 10 daqiqada so'rov yuboradi
    while True:
        try:
            time.sleep(600) # 10 daqiqa
            url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/"
            requests.get(url)
            logger.info("Ping yuborildi: Bot uyg'oq.")
        except Exception as e:
            logger.error(f"Ping xatosi: {e}")

# Threadlarni ishga tushirish
Thread(target=run_flask, daemon=True).start()
Thread(target=keep_alive, daemon=True).start()

# 4. BOT SOZLAMALARI
TOKEN = '7011547936:AAHFfUyzTg9EUhnq6KrKEP69pOm_uTHn-7Q'
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
ADMIN_LOGIN = "azik1202"
active_admins = set()

# 5. DATABASE (movies.db)
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT PRIMARY KEY, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# 6. KOMANDALAR VA FUNKSIYALAR
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="list_movies"))
    bot.send_message(message.chat.id, "Salom! Kino kodini yuboring yoki ro'yxatni ko'ring.", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def ask_login(message):
    bot.send_message(message.chat.id, "🔐 Loginni kiriting:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        active_admins.add(message.from_user.id)
        bot.reply_to(message, "✅ Admin tasdiqlandi! /add yoki /remove ishlata olasiz.")
    else:
        bot.reply_to(message, "❌ Xato.")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in active_admins: return
    if message.reply_to_message and message.reply_to_message.video:
        msg = bot.reply_to(message, "ID va Nomini yuboring (Masalan: `101 Qasoskorlar`)")
        bot.register_next_step_handler(msg, process_add, message.reply_to_message.video.file_id)
    else:
        bot.reply_to(message, "⚠️ Videoga reply qiling!")

def process_add(message, file_id):
    try:
        parts = message.text.split(maxsplit=1)
        db.execute("INSERT OR REPLACE INTO movies VALUES (?,?,?)", (parts[0], parts[1], file_id))
        db.commit()
        bot.send_message(message.chat.id, f"✅ Saqlandi: {parts[1]}")
    except:
        bot.send_message(message.chat.id, "❌ Xato format.")

@bot.message_handler(commands=['remove'])
def remove_movie(message):
    if message.from_user.id not in active_admins: return
    parts = message.text.split()
    if len(parts) > 1:
        db.execute("DELETE FROM movies WHERE m_id=?", (parts[1],))
        db.commit()
        bot.reply_to(message, f"✅ ID {parts[1]} o'chirildi.")

@bot.callback_query_handler(func=lambda call: call.data == "list_movies")
def show_list(call):
    rows = db.execute("SELECT m_id, m_name FROM movies").fetchall()
    text = "🎬 **Kinolar:**\n\n" + "\n".join([f"`{r[0]}` - {r[1]}" for r in rows]) if rows else "Hozircha bo'sh."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def search(message):
    query = message.text
    res = db.execute("SELECT f_id, m_name FROM movies WHERE m_id=? OR m_name LIKE ?", (query, f'%{query}%')).fetchone()
    if res:
        bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else:
        bot.send_message(message.chat.id, "🔍 Topilmadi.")

# 7. BOTNI QAYTA ISHGA TUSHIRISH TIZIMI
while True:
    try:
        logger.info("Bot ishga tushdi...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")
        time.sleep(5) # 5 soniya kutib qayta ulanadi
