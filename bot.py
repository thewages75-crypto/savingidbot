import telebot
import psycopg2
import random
import string
import os
# ==============================
# TELEGRAM ALBUM MEDIA TYPES
# ==============================

from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
albums = {}
ADMIN_ID = 8305774350
# ==============================
# MEDIA BUFFER SYSTEM
# ==============================

import threading
import time

media_buffer = {}
# ==============================
# SEND QUEUE SYSTEM
# ==============================

from queue import Queue

send_queue = Queue()

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

#====================
# GENRATE KEY
#====================
conn.commit()
def generate_vault_key():
    return "SPIDER-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
# ==============================
# GET USER VAULT FUNCTION
# ==============================

def get_user_vault(user_id):
    """
    Returns the vault key for a user session
    """
    cur.execute("SELECT vault_key FROM sessions WHERE user_id=%s", (user_id,))
    result = cur.fetchone()

    if result:
        return result[0]

    return None
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

# ==============================
# SEND WORKER (RATE LIMIT)
# ==============================

def send_worker():

    while True:

        func, args = send_queue.get()

        try:
            func(*args)

        except Exception as e:
            print("Send error:", e)

        time.sleep(0.04)  # about 25 messages per second

        send_queue.task_done()


threading.Thread(target=send_worker, daemon=True).start()
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
# ==============================
# ADMIN PANEL KEYBOARD
# ==============================

def admin_panel_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("📤 Export DB"),
        KeyboardButton("📥 Import DB")
    )

    kb.row(
        KeyboardButton("📊 Bot Stats"),
        KeyboardButton("🗂 Total Vaults")
    )

    kb.row(
        KeyboardButton("📦 Total Media")
    )

    kb.row(
        KeyboardButton("⬅ Back")
    )

    return kb
# ==============================
# ADMIN PANEL BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "⚙️ Admin Panel")
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        "⚙️ Admin Control Panel",
        reply_markup=admin_panel_menu()
    )
# ==============================
# BACK BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "⬅ Back")
def back_menu(message):

    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "Main Menu",
            reply_markup=admin_menu()
        )

    else:
        bot.send_message(
            message.chat.id,
            "Main Menu",
            reply_markup=user_menu()
        )
# ==============================
# TOTAL VAULTS
# ==============================

@bot.message_handler(func=lambda message: message.text == "🗂 Total Vaults")
def total_vaults(message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM vaults")
    count = cur.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"🗂 Total Vaults: {count}"
    )
# ==============================
# TOTAL MEDIA
# ==============================

@bot.message_handler(func=lambda message: message.text == "📦 Total Media")
def total_media(message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM media")
    count = cur.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📦 Total Stored Media: {count}"
    )
# ==============================
# BOT STATS
# ==============================

@bot.message_handler(func=lambda message: message.text == "📊 Bot Stats")
def bot_stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM vaults")
    vaults = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM media")
    media = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM sessions")
    sessions = cur.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 Bot Statistics\n\n"
        f"Vaults: {vaults}\n"
        f"Total Media: {media}\n"
        f"Active Sessions: {sessions}"
    )
# ==============================
# SAFE SEND FUNCTIONS
# ==============================

def safe_send_photo(chat_id, file_id):
    send_queue.put((bot.send_photo, (chat_id, file_id)))


def safe_send_video(chat_id, file_id):
    send_queue.put((bot.send_video, (chat_id, file_id)))


def safe_send_document(chat_id, file_id):
    send_queue.put((bot.send_document, (chat_id, file_id)))


def safe_send_animation(chat_id, file_id):
    send_queue.put((bot.send_animation, (chat_id, file_id)))


def safe_send_audio(chat_id, file_id):
    send_queue.put((bot.send_audio, (chat_id, file_id)))


def safe_send_voice(chat_id, file_id):
    send_queue.put((bot.send_voice, (chat_id, file_id)))


def safe_send_sticker(chat_id, file_id):
    send_queue.put((bot.send_sticker, (chat_id, file_id)))
# ==============================
# EXPORT DATABASE
# ==============================

import csv

@bot.message_handler(func=lambda message: message.text == "📤 Export DB")
def export_db(message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM media")
    rows = cur.fetchall()

    filename = "media_export.csv"

    with open(filename, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["id", "vault_key", "file_id", "media_type", "uploaded_at"])

        writer.writerows(rows)

    with open(filename, "rb") as f:
        bot.send_document(message.chat.id, f)
# ==============================
# IMPORT DATABASE
# ==============================

waiting_import = False

@bot.message_handler(func=lambda message: message.text == "📥 Import DB")
def import_db(message):

    global waiting_import

    if message.from_user.id != ADMIN_ID:
        return

    waiting_import = True

    bot.send_message(
        message.chat.id,
        "Send the CSV backup file."
    )


@bot.message_handler(content_types=['document'])
def receive_import(message):

    global waiting_import

    if not waiting_import:
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)

    with open("import.csv", "wb") as f:
        f.write(downloaded)

    with open("import.csv", newline="") as f:

        reader = csv.reader(f)

        next(reader)

        for row in reader:

            cur.execute(
                "INSERT INTO media (id,vault_key,file_id,media_type,uploaded_at) VALUES (%s,%s,%s,%s,%s)",
                row
            )

    conn.commit()

    waiting_import = False

    bot.send_message(message.chat.id, "Database imported successfully.")
@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    # check if user already has a session
    cur.execute("SELECT vault_key FROM sessions WHERE user_id=%s", (user_id,))
    result = cur.fetchone()

    if result:
        vault_key = result[0]

    else:
        vault_key = generate_vault_key()

        cur.execute(
            "INSERT INTO vaults (vault_key) VALUES (%s)",
            (vault_key,)
        )

        cur.execute(
            "INSERT INTO sessions (user_id, vault_key) VALUES (%s,%s)",
            (user_id, vault_key)
        )

        conn.commit()

    if user_id == ADMIN_ID:

        bot.send_message(
            message.chat.id,
            f"📦 Media Vault\n\nAdmin Vault Key:\n{vault_key}",
            reply_markup=admin_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            f"📦 Media Vault\n\nYour Vault Key:\n{vault_key}\n\nSave this key safely.",
            reply_markup=user_menu()
        )        
@bot.message_handler(commands=['login'])
def login(message):

    try:
        key = message.text.split()[1]

    except:
        bot.reply_to(message, "Usage:\n/login VAULT_KEY")
        return

    cur.execute("SELECT vault_key FROM vaults WHERE vault_key=%s", (key,))
    result = cur.fetchone()

    if not result:
        bot.reply_to(message, "Invalid vault key.")
        return

    user_id = message.from_user.id

    cur.execute("""
    INSERT INTO sessions (user_id, vault_key)
    VALUES (%s,%s)
    ON CONFLICT (user_id)
    DO UPDATE SET vault_key=EXCLUDED.vault_key
    """, (user_id, key))

    conn.commit()

    bot.reply_to(message, "Vault connected successfully.")
# ==============================
# MEDIA HANDLER
# ==============================

# ==============================
# MEDIA HANDLER (ALBUM SUPPORT)
# ==============================

# ==============================
# MEDIA HANDLER WITH BUFFER
# ==============================

@bot.message_handler(content_types=[
    'photo','video','document','animation',
    'audio','voice','sticker'
])
def handle_media(message):

    user_id = message.from_user.id
    vault_key = get_user_vault(user_id)

    if not vault_key:
        bot.reply_to(message, "You are not connected to a vault.")
        return

    # detect media
    file_id = None
    media_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"

    elif message.video:
        file_id = message.video.file_id
        media_type = "video"

    elif message.document:
        file_id = message.document.file_id
        media_type = "document"

    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"

    elif message.audio:
        file_id = message.audio.file_id
        media_type = "audio"

    elif message.voice:
        file_id = message.voice.file_id
        media_type = "voice"

    elif message.sticker:
        file_id = message.sticker.file_id
        media_type = "sticker"

    group_id = message.media_group_id or message.message_id

    # create buffer for user
    if user_id not in media_buffer:
        media_buffer[user_id] = {}

    if group_id not in media_buffer[user_id]:
        media_buffer[user_id][group_id] = {
            "vault_key": vault_key,
            "items": [],
            "timestamp": time.time()
        }

    media_buffer[user_id][group_id]["items"].append((file_id, media_type))
# ==============================
# MEDIA PROCESSOR
# ==============================

def process_media():

    while True:

        time.sleep(3)

        now = time.time()

        for user_id in list(media_buffer.keys()):

            for group_id in list(media_buffer[user_id].keys()):

                data = media_buffer[user_id][group_id]

                if now - data["timestamp"] < 3:
                    continue

                vault_key = data["vault_key"]
                items = data["items"]

                # store media
                for file_id, media_type in items:

                    cur.execute(
                        """
                        INSERT INTO media
                        (vault_key,file_id,media_type,media_group_id)
                        VALUES (%s,%s,%s,%s)
                        """,
                        (vault_key, file_id, media_type, str(group_id))
                    )

                conn.commit()

                # send confirmation
                bot.send_message(
                    user_id,
                    f"✅ Stored {len(items)} media successfully."
                )

                del media_buffer[user_id][group_id]

        time.sleep(1)


threading.Thread(target=process_media, daemon=True).start()
# ==============================
# PROCESS ALBUMS
# ==============================

import threading
import time

def process_albums():

    while True:

        time.sleep(2)

        if not albums:
            continue

        for group_id in list(albums.keys()):

            items = albums.pop(group_id)

            for vault_key, file_id, media_type in items:

                cur.execute(
                    "INSERT INTO media (vault_key, file_id, media_type) VALUES (%s,%s,%s)",
                    (vault_key, file_id, media_type)
                )

            conn.commit()


threading.Thread(target=process_albums, daemon=True).start()
# ==============================
# MEDIA PAGINATION FUNCTION
# ==============================

# ==============================
# MEDIA VIEWER WITH ALBUM SUPPORT
# ==============================

def send_media_page(chat_id, vault_key, page=0):

    limit = 10
    offset = page * limit

    cur.execute("""
        SELECT file_id, media_type, media_group_id
        FROM media
        WHERE vault_key=%s
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, (vault_key, limit, offset))

    rows = cur.fetchall()

    if not rows:
        bot.send_message(chat_id, "No media stored.")
        return

    albums = {}
    singles = []

    # group albums
    for file_id, media_type, group_id in rows:

        if group_id:

            if group_id not in albums:
                albums[group_id] = []

            albums[group_id].append((file_id, media_type))

        else:
            singles.append((file_id, media_type))

    # send albums
    for group_id, items in albums.items():

        media_group = []

        for file_id, media_type in items:

            if media_type == "photo":
                media_group.append(InputMediaPhoto(file_id))

            elif media_type == "video":
                media_group.append(InputMediaVideo(file_id))

            elif media_type == "document":
                media_group.append(InputMediaDocument(file_id))

        if media_group:
            send_queue.put((bot.send_media_group, (chat_id, media_group)))

    # send single media
    for file_id, media_type in singles:

        if media_type == "photo":
            safe_send_photo(chat_id, file_id)

        elif media_type == "video":
            safe_send_video(chat_id, file_id)

        elif media_type == "document":
            safe_send_document(chat_id, file_id)

        elif media_type == "animation":
            safe_send_animation(chat_id, file_id)

        elif media_type == "audio":
            safe_send_audio(chat_id, file_id)

        elif media_type == "voice":
            safe_send_voice(chat_id, file_id)

        elif media_type == "sticker":
            safe_send_sticker(chat_id, file_id)

    # navigation buttons
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("⬅ Previous", callback_data=f"media_{page-1}"),
        InlineKeyboardButton("➡ Next", callback_data=f"media_{page+1}")
    )

    bot.send_message(chat_id, f"Page {page+1}", reply_markup=markup)
# ==============================
# MY MEDIA BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "📁 My Media")
def my_media(message):

    user_id = message.from_user.id

    vault_key = get_user_vault(user_id)

    if not vault_key:
        bot.reply_to(message, "You are not connected to a vault.")
        return

    send_media_page(message.chat.id, vault_key, page=0)
# ==============================
# PAGINATION CALLBACK
# ==============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("media_"))
def media_pages(call):

    page = int(call.data.split("_")[1])

    if page < 0:
        return

    user_id = call.from_user.id
    vault_key = get_user_vault(user_id)

    send_media_page(call.message.chat.id, vault_key, page)
# ==============================
# MY KEY BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "🔑 My Key")
def show_key(message):

    user_id = message.from_user.id

    vault_key = get_user_vault(user_id)

    if not vault_key:
        bot.reply_to(message, "You are not connected to a vault.")
        return

    bot.send_message(
        message.chat.id,
        f"🔑 Your Vault Key:\n\n{vault_key}\n\nKeep this key safe."
    )
# ==============================
# VAULT STATS BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "📊 Vault Stats")
def vault_stats(message):

    user_id = message.from_user.id

    vault_key = get_user_vault(user_id)

    if not vault_key:
        bot.reply_to(message, "You are not connected to a vault.")
        return

    # total media count
    cur.execute(
        "SELECT COUNT(*) FROM media WHERE vault_key=%s",
        (vault_key,)
    )

    total_media = cur.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 Vault Statistics\n\nTotal Media Stored: {total_media}"
    )
# ==============================
# HELP BUTTON
# ==============================

@bot.message_handler(func=lambda message: message.text == "❓ Help")
def help_menu(message):

    bot.send_message(
        message.chat.id,
        "📦 Media Vault Bot\n\n"
        "Send any media to store it in your vault.\n\n"
        "Commands:\n"
        "/start - create vault\n"
        "/login <key> - access vault from another account\n\n"
        "Use the buttons below to manage your vault."
    )
print("Bot running...")

bot.infinity_polling()
