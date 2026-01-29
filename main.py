import telebot
import sqlite3

# --- 1. SOZLAMALAR ---
TOKEN = '7011547936:AAFqL1gzd_nczMiMllwgoGigoUQrNIUk2o0' # O'zingiznikini qo'ying
bot = telebot.TeleBot(TOKEN)
ADMIN_LOGIN = "azik1202"
admins = set()

# --- 2. MA'LUMOTLAR BAZASI (XAVFSIZ USUL) ---
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    # Jadval va ustunlarni tekshirib yaratadi
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# --- 3. FOYDALANUVCHI QISMI ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="list"))
    bot.send_message(message.chat.id, f"Assalomu aleykum {message.from_user.first_name}!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "list")
def list_mov(call):
    cursor = db.cursor()
    cursor.execute("SELECT m_id, m_name FROM movies")
    rows = cursor.fetchall()
    text = "🎬 Kinolar:\n\n" + "\n".join([f"{r[0]}. {r[1]}" for r in rows]) if rows else "Hozircha bo'sh."
    bot.send_message(call.message.chat.id, text)

# --- 4. ADMIN VA QIDIRUV ---
@bot.message_handler(commands=['admin'])
def adm(message):
    bot.send_message(message.chat.id, "Login?")
    bot.register_next_step_handler(message, lambda m: admins.add(m.from_user.id) or bot.reply_to(m, "Admin faol!") if m.text == ADMIN_LOGIN else bot.reply_to(m, "Xato!"))

@bot.message_handler(commands=['add'])
def add(message):
    if message.from_user.id in admins and message.reply_to_message and message.reply_to_message.video:
        p = message.text.split(maxsplit=2)
        if len(p) < 3: return bot.reply_to(message, "Format: /add ID NOMI")
        db.execute("INSERT INTO movies VALUES (?,?,?)", (p[1], p[2], message.reply_to_message.video.file_id))
        db.commit()
        bot.reply_to(message, "✅ Qo'shildi!")

@bot.message_handler(func=lambda m: m.text.isdigit())
def find(message):
    res = db.execute("SELECT f_id, m_name FROM movies WHERE m_id=?", (message.text,)).fetchone()
    if res: bot.send_video(message.chat.id, res[0], caption=res[1])
    else: bot.send_message(message.chat.id, "Topilmadi.")

bot.infinity_polling()
