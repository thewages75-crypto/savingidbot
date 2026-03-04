import telebot
import psycopg2
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_ID = 8305774350

# DATABASE_URL = "postgresql://user:password@localhost:5432/media_db"

bot = telebot.TeleBot(BOT_TOKEN)

# Database connection
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Database connected...")

cur.execute("""
CREATE TABLE IF NOT EXISTS vaults(
id SERIAL PRIMARY KEY,
vault_key TEXT UNIQUE,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS media(
id SERIAL PRIMARY KEY,
vault_key TEXT,
file_id TEXT,
media_type TEXT,
uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sessions(
user_id BIGINT PRIMARY KEY,
vault_key TEXT
)
""")

conn.commit()


def user_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("📁 My Media"),
        KeyboardButton("🔑 My Key")
    )

    kb.row(
        KeyboardButton("📊 Vault Stats"),
        KeyboardButton("❓ Help")
    )

    return kb


def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("📁 My Media"),
        KeyboardButton("🔑 My Key")
    )

    kb.row(
        KeyboardButton("📊 Vault Stats"),
        KeyboardButton("❓ Help")
    )

    kb.row(
        KeyboardButton("⚙️ Admin Panel")
    )

    return kb
@bot.message_handler(commands=['start'])
def start(message):

    if message.from_user.id == ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "📦 Media Vault\n\nWelcome Admin.",
            reply_markup=admin_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            "📦 Media Vault\n\nSend media to store it.",
            reply_markup=user_menu()
        )
        
print("Bot running...")

bot.infinity_polling()
