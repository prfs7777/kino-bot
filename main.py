import telebot
import sqlite3

# --- 1. SOZLAMALAR ---
TOKEN = '7011547936:AAFqL1gzd_nczMiMllwgoGigoUQrNIUk2o0' # BotFather bergan tokenni qo'ying
bot = telebot.TeleBot(TOKEN)
ADMIN_LOGIN = "azik1202" # Adminlik uchun maxfiy so'z
admins = set() # Admin bo'lganlarni eslab qolish uchun

# --- 2. MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    # Jadval: ID, Nomi, Telegram File ID
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# --- 3. ADMIN TIZIMI (LOGIN/ADD/REMOVE) ---

@bot.message_handler(commands=['admin'])
def admin_start(message):
    bot.send_message(message.chat.id, "Maxfiy loginni kiriting:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        admins.add(message.from_user.id)
        bot.reply_to(message, "✅ Xush kelibsiz, Admin! \n\n/add [id] [nomi] - Kino qo'shish\n/remove [id] - O'chirish")
    else:
        bot.reply_to(message, "❌ Login xato!")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in admins:
        return bot.reply_to(message, "Siz admin emassiz!")
    
    if message.reply_to_message and message.reply_to_message.video:
        try:
            parts = message.text.split()
            m_id = parts[1] # Masalan: 1
            m_name = " ".join(parts[2:]) # Masalan: Forsaj 10
            f_id = message.reply_to_message.video.file_id
            
            cursor = db.cursor()
            cursor.execute("INSERT INTO movies (m_id, m_name, f_id) VALUES (?,?,?)", (m_id, m_name, f_id))
            db.commit()
            bot.reply_to(message, f"✅ Bazaga qo'shildi:\nID: {m_id}\nNomi: {m_name}")
        except:
            bot.reply_to(message, "Xato! Format: /add 1 Forsaj 10 (Videoga reply qilib yozing)")
    else:
        bot.reply_to(message, "Videoga reply (javob) qilib yozing!")

@bot.message_handler(commands=['remove'])
def remove_movie(message):
    if message.from_user.id not in admins: return
    try:
        m_id = message.text.split()[1]
        cursor = db.cursor()
        cursor.execute("DELETE FROM movies WHERE m_id=?", (m_id,))
        db.commit()
        bot.reply_to(message, f"🗑 ID {m_id} o'chirildi.")
    except:
        bot.reply_to(message, "Format: /remove 1")

# --- 4. FOYDALANUVCHILAR UCHUN ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🎬 Mavjud kinolar", callback_data="list_movies")
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        f"Assalomu aleykum {user_name}, xush kelibsiz telegram botimizga!", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "list_movies")
def show_list(call):
    cursor = db.cursor()
    cursor.execute("SELECT m_id, m_name FROM movies")
    data = cursor.fetchall()
    
    if data:
        text = "🎬 **Kinolar ro'yxati:**\n\n"
        for row in data:
            text += f"🆔 {row[0]} — 🎥 {row[1]}\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "Hozircha bazada kinolar yo'q.")

@bot.message_handler(func=lambda m: m.text.isdigit())
def search_movie(message):
    cursor = db.cursor()
    cursor.execute("SELECT f_id, m_name FROM movies WHERE m_id=?", (message.text,))
    res = cursor.fetchone()
    if res:
        bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else:
        bot.send_message(message.chat.id, "Kino topilmadi.")

print("Bot ishlamoqda...")
bot.infinity_polling()
