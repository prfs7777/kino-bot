import os
import sqlite3
import logging
from flask import Flask
from threading import Thread
import telebot

# 1. LOGGING SOZLAMALARI (Render loglarida xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. RENDER UCHUN VEB-SERVER (PORT ALDASH)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running and healthy!", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Flaskni alohida thread'da yurgizamiz
Thread(target=run_flask, daemon=True).start()

# 3. BOT SOZLAMALARI
TOKEN = '7011547936:AAHFfUyzTg9EUhnq6KrKEP69pOm_uTHn-7Q'
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
ADMIN_LOGIN = "azik1202"
active_admins = set()
@bot.message_handler(commands=['remove'])
def remove_movie(message):
    # Adminlikni tekshirish
    if message.from_user.id not in active_admins:
        bot.reply_to(message, "🛑 Siz admin emassiz!")
        return
    
    # Buyruqdan keyin ID yozilganini tekshirish
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ O'chirish uchun ID yuboring. Masalan: `/remove 101`")
            return
            
        m_id = parts[1]
        
        # Bazadan o'chirish
        cursor = db.cursor()
        cursor.execute("DELETE FROM movies WHERE m_id=?", (m_id,))
        db.commit()
        
        if cursor.rowcount > 0:
            bot.reply_to(message, f"✅ ID `{m_id}` bo'lgan kino bazadan o'chirildi.")
        else:
            bot.reply_to(message, f"❓ Bazada `{m_id}` ID bilan kino topilmadi.")
            
    except Exception as e:
        bot.reply_to(message, "❌ Xatolik yuz berdi.")
        logger.error(f"Remove error: {e}")
# 4. DATABASE BILAN ISHLASH (Xavfsiz ulanish)
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
        bot.reply_to(message, "✅ Admin huquqlari berildi!\n\n/add - Kino qo'shish\n/list - Ro'yxat")
    else:
        bot.reply_to(message, "❌ Login noto'g'ri!")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in active_admins:
        bot.reply_to(message, "🛑 Siz admin emassiz!")
        return
    
    if message.reply_to_message and message.reply_to_message.video:
        msg = bot.reply_to(message, "Kino ID va nomini yuboring (Masalan: `101 Qasoskorlar`)")
        bot.register_next_step_handler(msg, process_add_movie, message.reply_to_message.video.file_id)
    else:
        bot.reply_to(message, "⚠️ Videoga reply (javob) qilib /add yozishingiz kerak!")

def process_add_movie(message, file_id):
    try:
        parts = message.text.split(maxsplit=1)
        m_id = parts[0]
        m_name = parts[1]
        
        cursor = db.cursor()
        cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?, ?)", (m_id, m_name, file_id))
        db.commit()
        bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli saqlandi:\n🆔 ID: {m_id}\n🎥 Nomi: {m_name}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Xatolik! Formatni tekshiring: `ID NOMI` (Masalan: `10 Qasoskorlar`)")
        logger.error(f"Add movie error: {e}")

# 6. FOYDALANUVCHILAR UCHUN
@bot.message_handler(commands=['start'])
def welcome(message):
    user = message.from_user.first_name
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="list_movies"))
    bot.send_message(message.chat.id, f"Assalomu aleykum *{user}*!\n\nKino kodini yuboring yoki ro'yxatni ko'ring.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "list_movies")
def show_list(call):
    cursor = db.cursor()
    cursor.execute("SELECT m_id, m_name FROM movies")
    rows = cursor.fetchall()
    
    if rows:
        text = "🎬 **Mavjud kinolar:**\n\n"
        for r in rows:
            text += f"🆔 `{r[0]}` — {r[1]}\n"
    else:
        text = "📭 Baza hozircha bo'sh."
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def search_movie(message):
    # Faqat raqam bo'lsa ID bo'yicha, matn bo'lsa nomi bo'yicha qidiradi
    query = message.text
    cursor = db.cursor()
    
    if query.isdigit():
        res = cursor.execute("SELECT f_id, m_name FROM movies WHERE m_id=?", (query,)).fetchone()
    else:
        res = cursor.execute("SELECT f_id, m_name FROM movies WHERE m_name LIKE ?", (f'%{query}%',)).fetchone()

    if res:
        bot.send_video(message.chat.id, res[0], caption=f"🎬 **{res[1]}**\n\n@kino_botingiz")
    else:
        bot.send_message(message.chat.id, "🔍 Afsuski, bunday kino topilmadi.")

# BOTNI ISHGA TUSHIRISH
if __name__ == '__main__':
    logger.info("Bot is starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

