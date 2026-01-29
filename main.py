import telebot
import sqlite3

TOKEN = '7011547936:AAFBU2KE-USyAofoh1P9LH3_37Qkz_z-17w'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 123456789 # O'zingni Telegram ID raqamingni yoz (ixtiyoriy)


# Admin ma'lumotlari
ADMIN_LOGIN = "azik1202"
admins = set() # Bot o'chib yonguncha adminlarni eslab qoladi

# Bazani sozlash (ID va Nomi bilan)
def init_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT, m_name TEXT, f_id TEXT)')
    conn.commit()
    return conn

db = init_db()

# --- FOYDALANUVCHILAR UCHUN ---

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user.first_name
    # Inline button yaratish
    markup = telebot.types.InlineKeyboardMarkup()
    news_btn = telebot.types.InlineKeyboardButton("🎬 Kinolar ro'yxati", callback_data="show_news")
    markup.add(news_btn)
    
    bot.send_message(message.chat.id, f"Assalomu aleykum {user}, xush kelibsiz telegram botimizga!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_news")
def news(call):
    cursor = db.cursor()
    cursor.execute("SELECT m_id, m_name FROM movies")
    data = cursor.fetchall()
    
    if data:
        text = "🎬 **Mavjud kinolar:**\n\n"
        for row in data:
            text += f"🆔 {row[0]} | 🎥 {row[1]}\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "Hozircha kinolar yo'q.")

# --- ADMIN TIZIMI ---

@bot.message_handler(commands=['admin'])
def admin_login(message):
    bot.send_message(message.chat.id, "Maxfiy loginni kiriting:")
    bot.register_next_step_handler(message, check_login)

def check_login(message):
    if message.text == ADMIN_LOGIN:
        admins.add(message.from_user.id)
        bot.reply_to(message, "Xush kelibsiz, Admin! Endi /add va /remove buyruqlari ishlaydi.")
    else:
        bot.reply_to(message, "Login xato! Siz admin emassiz.")

# Kino qo'shish (Faqat admin uchun)
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id not in admins:
        return bot.reply_to(message, "Bu buyruq faqat adminlar uchun!")
    
    if message.reply_to_message and message.reply_to_message.video:
        try:
            # Format: /add 1 Forsaj_10
            parts = message.text.split()
            m_id = parts[1]
            m_name = " ".join(parts[2:])
            f_id = message.reply_to_message.video.file_id
            
            cursor = db.cursor()
            cursor.execute("INSERT INTO movies VALUES (?,?,?)", (m_id, m_name, f_id))
            db.commit()
            bot.reply_to(message, f"✅ Qo'shildi!\nID: {m_id}\nNomi: {m_name}")
        except:
            bot.reply_to(message, "Xato! Format: /add [id] [nomi] (videoga reply qiling)")
    else:
        bot.reply_to(message, "Videoga reply qilib yozing!")

# Kinoni o'chirish
@bot.message_handler(commands=['remove'])
def remove_movie(message):
    if message.from_user.id not in admins:
        return
    try:
        m_id = message.text.split()[1]
        cursor = db.cursor()
        cursor.execute("DELETE FROM movies WHERE m_id=?", (m_id,))
        db.commit()
        bot.reply_to(message, f"🗑 ID {m_id} bazadan o'chirildi.")
    except:
        bot.reply_to(message, "Format: /remove [id]")

# Kino qidirish (Oddiy foydalanuvchi uchun)
@bot.message_handler(func=lambda m: m.text.isdigit())
def search(message):
    cursor = db.cursor()
    cursor.execute("SELECT f_id, m_name FROM movies WHERE m_id=?", (message.text,))
    data = cursor.fetchone()
    if data:
        bot.send_video(message.chat.id, data[0], caption=f"🎬 {data[1]}")
    else:
        bot.send_message(message.chat.id, "Kino topilmadi.")

bot.infinity_polling()

