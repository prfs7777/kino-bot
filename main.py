import telebot
import sqlite3

TOKEN = '7011547936:AAFBU2KE-USyAofoh1P9LH3_37Qkz_z-17w'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 123456789 # O'zingni Telegram ID raqamingni yoz (ixtiyoriy)

# Bazani sozlash
def get_db():
    conn = sqlite3.connect('movies.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS movies (m_id TEXT, f_id TEXT)')
    return conn

db = get_db()

# 1. Foydalanuvchi raqam yozsa (Masalan: 1)
@bot.message_handler(func=lambda m: m.text.isdigit())
def get_movie(message):
    cursor = db.cursor()
    cursor.execute("SELECT f_id FROM movies WHERE m_id=?", (message.text,))
    data = cursor.fetchone()
    if data:
        bot.send_video(message.chat.id, data[0], caption=f"Kino ID: {message.text}")
    else:
        bot.send_message(message.chat.id, "Kino topilmadi.")

# 2. ADMIN UCHUN PULT: Kino qo'shish (/add 1)
# Kinoni botga yuborasiz, keyin unga javob (reply) qilib /add 1 deb yozasiz
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.reply_to_message and message.reply_to_message.video:
        movie_number = message.text.split()[1]
        file_id = message.reply_to_message.video.file_id
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO movies (m_id, f_id) VALUES (?,?)", (movie_number, file_id))
        db.commit()
        bot.reply_to(message, f"Tayyor! Endi {movie_number} yozsa, shu kino chiqadi.")
    else:
        bot.reply_to(message, "Xato! Kinoni yuboring va unga reply qilib '/add raqam' deb yozing.")


bot.infinity_polling()
