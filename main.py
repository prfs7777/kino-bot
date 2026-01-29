import os
import sqlite3
import logging
from flask import Flask
from threading import Thread
import telebot

# 1. LOGGING (Render loglarida ko'rish uchun)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. RENDER UCHUN PORT ALDASH
app = Flask('')
@app.route('/')
def home(): return "Bot is live!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000)) # Senda 10000-port ishladi
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

# 3. BOT SOZLAMALARI
TOKEN = '7011547936:AAHFfUyzTg9EUhnq6KrKEP69pOm_uTHn-7Q'
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
ADMIN_LOGIN = "azik1202"
active_admins = set()

# 4. BAZA BILAN ISHLASH
def get_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT PRIMARY KEY, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = get_db()

# 5. ADMIN KOMANDALARI
@bot.message_handler(commands=['admin'])
def ask_login(message):
    bot.send_message(message.chat.id, "🔐 Maxfiy loginni kiriting:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        active_admins.add(message.from_user.id)
        bot.reply_to(message, "✅ Admin tasdiqlandi!\n\n/add - Qo'shish\n/remove ID - O'chirish")
    else:
        bot.reply_to(message, "❌ Login xato!")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in active_admins: return
    if message.reply_to_message and message.reply_to_message.video:
        msg = bot.reply_to(message, "Kino ID va nomini yuboring (Masalan: `101 Qasoskorlar`)")
        bot.register_next_step_handler(msg, process_add_movie, message.reply_to_message.video.file_id)
    else:
        bot.reply_to(message, "⚠️ Videoga reply qilib /add yozing!")

def process_add_movie(message, file_id):
    try:
        parts = message.text.split(maxsplit=1)
        m_id, m_name = parts[0], parts[1]
        db.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (m_id, m_name, file_id))
        db.commit()
        bot.send_message(message.chat.id, f"✅ Saqlandi: {m_name}")
    except:
        bot.send_message(message.chat.id, "❌ Xato! Format: `ID NOMI`")

# --- YANGI REMOVE FUNKSIYASI ---
@bot.message_handler(commands=['remove'])
def remove_movie(message):
    if message.from_user.id not in active_admins:
        bot.reply_to(message, "🛑 Admin emassiz!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ ID kiriting. Masalan: `/remove 101`")
        return
        
    m_id = parts[1]
    cursor = db.cursor()
    cursor.execute("DELETE FROM movies WHERE m_id=?", (m_id,))
    db.commit()
    
    if cursor.rowcount > 0:
        bot.reply_to(message, f"✅ ID `{m_id}` bazadan o'chirildi.")
    else:
        bot.reply_to(message, "🔍 Bunday ID topilmadi.")

# 6. FOYDALANUVCHILAR UCHUN
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="list_movies"))
    bot.send_message(message.chat.id, f"Salom! Kino kodini yuboring.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "list_movies")
def show_list(call):
    cursor = db.cursor()
    rows = cursor.execute("SELECT m_id, m_name FROM movies").fetchall()
    text = "🎬 **Kinolar:**\n\n" + "\n".join([f"`{r[0]}` - {r[1]}" for r in rows]) if rows else "Bo'sh."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def search(message):
    query = message.text
    res = db.execute("SELECT f_id, m_name FROM movies WHERE m_id=? OR m_name LIKE ?", (query, f'%{query}%')).fetchone()
    if res: bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else: bot.send_message(message.chat.id, "🔍 Topilmadi.")

bot.infinity_polling()
