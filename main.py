import telebot
import sqlite3

# --- 1. SOZLAMALAR ---
TOKEN = '7011547936:AAGGR0G_jxDiCarlPwRPR35hf5i_y6xAeNE'
bot = telebot.TeleBot(TOKEN)
ADMIN_LOGIN = "azik1202"
admins = set()

# --- 2. BAZANI SOZLASH ---
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# --- 3. FOYDALANUVCHILAR UCHUN ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user = message.from_user.first_name
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="list"))
    bot.send_message(message.chat.id, f"Assalomu aleykum {user}, xush kelibsiz!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "list")
def show_list(call):
    cursor = db.cursor()
    cursor.execute("SELECT m_id, m_name FROM movies")
    rows = cursor.fetchall()
    text = "🎬 **Mavjud kinolar:**\n\n" + "\n".join([f"🆔 {r[0]} | 🎥 {r[1]}" for r in rows]) if rows else "Baza hozircha bo'sh."
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# --- 4. ADMIN TIZIMI ---
@bot.message_handler(commands=['admin'])
def ask_login(message):
    bot.send_message(message.chat.id, "Maxfiy loginni kiriting:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        admins.add(message.from_user.id)
        bot.reply_to(message, "✅ Admin tasdiqlandi! /add va /remove ishlaydi.")
    else:
        bot.reply_to(message, "❌ Login xato!")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in admins: return
    if message.reply_to_message and message.reply_to_message.video:
        try:
            p = message.text.split(maxsplit=2)
            db.execute("INSERT INTO movies VALUES (?,?,?)", (p[1], p[2], message.reply_to_message.video.file_id))
            db.commit()
            bot.reply_to(message, f"✅ Qo'shildi: {p[2]}")
        except:
            bot.reply_to(message, "Xato! Format: /add ID NOMI (videoga reply qiling)")

@bot.message_handler(func=lambda m: m.text.isdigit())
def find(message):
    res = db.execute("SELECT f_id, m_name FROM movies WHERE m_id=?", (message.text,)).fetchone()
    if res: bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else: bot.send_message(message.chat.id, "Kino topilmadi.")

bot.infinity_polling()
