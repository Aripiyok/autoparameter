import os
import re
import base64
import logging
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ===========================
# LOAD .ENV
# ===========================
load_dotenv()

BOT_TOKEN       = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL  = int(os.getenv("SOURCE_CHANNEL"))
TARGET_CHANNEL  = int(os.getenv("TARGET_CHANNEL"))
BOT_USERNAME    = os.getenv("BOT_USERNAME")
DEFAULT_IMAGE   = os.getenv("DEFAULT_IMAGE", "foto.jpg")
MAIN_CHANNEL_ID = int(os.getenv("MAIN_CHANNEL_ID"))

# ===========================
# LOGGING
# ===========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ===========================
# FUNGSI REMOVE LINK
# ===========================
def remove_links(text: str):
    if not text:
        return text
    return re.sub(r'https?://\S+', '', text).strip()

# ===========================
# ENCODE / DECODE PARAM
# ===========================
def encode_param(message_id: int):
    raw = f"get-{message_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_param(encoded: str):
    decoded = base64.urlsafe_b64decode(encoded).decode()
    return int(decoded.replace("get-", ""))

# ===========================
# CEK JOIN
# ===========================
async def is_joined(user_id: int, context):
    try:
        member = await context.bot.get_chat_member(MAIN_CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ===========================
# KEYBOARD FORCE JOIN
# ===========================
def join_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔐 WELCOME APEM ANGET",
                url="https://t.me/infoviralhariini"
            )
        ],
        [
            InlineKeyboardButton("🔄 COBA LAGI", callback_data="retry")
        ]
    ])

# ===========================
# SHOW JOIN MESSAGE
# ===========================
async def show_join(update: Update):
    text = (
        "✨ *WELCOME MEK*\n\n"
        "Kamu *belum join channel wajib*.\n"
        "Setel join, pilih konten di daftar channel asupan*."
    )

    await update.effective_chat.send_message(
        text,
        parse_mode="Markdown",
        reply_markup=join_keyboard()
    )

# ===========================
# LISTENER SOURCE CHANNEL
# ===========================
async def channel_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg or msg.chat.id != SOURCE_CHANNEL:
        return

    cap_raw = msg.caption_html or msg.text_html or ""
    cap_clean = remove_links(cap_raw)
    encoded = encode_param(msg.message_id)

    teaser = (
        f"{cap_clean}\n\n"
        f"👉 <b>Buka konten lengkap:</b>\n"
        f"https://t.me/{BOT_USERNAME}?start={encoded}"
    )

    with open(DEFAULT_IMAGE, "rb") as img:
        await context.bot.send_photo(
            chat_id=TARGET_CHANNEL,
            photo=img,
            caption=teaser,
            parse_mode="HTML",
        )

# ===========================
# SEND ORIGINAL MESSAGE
# ===========================
async def send_original(context, chat_id, message_id):
    try:
        await context.bot.copy_messages(
            chat_id=chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_ids=[message_id]
        )
        return True
    except:
        pass

    try:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=SOURCE_CHANNEL,
            message_id=message_id
        )
        return True
    except:
        return False

# ===========================
# /START
# ===========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_joined(user_id, context):
        return await show_join(update)

    # jika tanpa parameter /start
    if not context.args:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📜 DAFTAR CHANNEL ASUPAN",
                    url="https://t.me/infoviralhariini"
                )
            ]
        ])

        return await update.message.reply_text(
            "✅ Kamu sudah join!\n\n"
            "Silakan pilih konten di *DAFTAR CHANNEL WELCOME MEK*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # jika pakai parameter
    try:
        msg_id = decode_param(context.args[0])
    except:
        return await update.message.reply_text("Parameter tidak valid.")

    await send_original(context, update.effective_chat.id, msg_id)

# ===========================
# COBA LAGI
# ===========================
async def retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_joined(user_id, context):
        return await show_join(update)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📜 DAFTAR CHANNEL ASUPAN",
                url="https://t.me/infoviralhariini"
            )
        ]
    ])

    await query.message.reply_text(
        "✅ Kamu sudah join!\n\n"
        "Silakan pilih konten di *DAFTAR CHANNEL WELCOME MEK*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ===========================
# MAIN
# ===========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(retry, pattern="retry"))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_listener))

    log.info("BOT AKTIF — FINAL FIX FORCE JOIN REAL")
    app.run_polling()

if __name__ == "__main__":
    main()

