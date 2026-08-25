"""بوت كليشة لفتح التطبيق المصغّر وتسجيل المستخدمين وإدارة البث."""
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway Variables: لا تضع التوكن داخل هذا الملف.
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "1427023555"))
MINI_APP_URL = os.getenv(
    "MINI_APP_URL", "https://hshahahaha.github.io/ayman-ph-website/#/collection/best-selling"
)
DB_PATH = Path(os.getenv("DB_PATH", "kaleesha_bot.db"))
START_IMAGE_PATH = Path(__file__).with_name("kaleesha_start_image.jpg")
WAITING_BROADCAST = 1


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )"""
        )


def register_user(tg_user) -> bool:
    """يعيد True فقط عند أول استخدام للمستخدم."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with db() as connection:
        existed = connection.execute("SELECT 1 FROM users WHERE user_id = ?", (tg_user.id,)).fetchone()
        connection.execute(
            """INSERT INTO users (user_id, first_name, username, first_seen, last_seen, is_active)
               VALUES (?, ?, ?, ?, ?, 1)
               ON CONFLICT(user_id) DO UPDATE SET
                 first_name = excluded.first_name,
                 username = excluded.username,
                 last_seen = excluded.last_seen,
                 is_active = 1""",
            (tg_user.id, tg_user.first_name, tg_user.username, now, now),
        )
    return existed is None


def mark_inactive(user_id: int) -> None:
    with db() as connection:
        connection.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))


def active_user_ids() -> list[int]:
    with db() as connection:
        return [row["user_id"] for row in connection.execute("SELECT user_id FROM users WHERE is_active = 1")]


def stats() -> tuple[int, int]:
    with db() as connection:
        total = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active = connection.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]
    return total, active


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📣 إرسال بث", callback_data="broadcast:menu")],
            [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="admin:stats")],
            [InlineKeyboardButton("🛍 فتح متجر كليشة", web_app=WebAppInfo(url=MINI_APP_URL))],
        ]
    )


async def notify_new_user(context: ContextTypes.DEFAULT_TYPE, tg_user) -> None:
    username = f"@{tg_user.username}" if tg_user.username else "لا يوجد"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        "🎉 مستخدم جديد في بوت كليشة\n\n"
        f"👤 الاسم: {tg_user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 User ID: {tg_user.id}\n"
        f"🕒 التاريخ والوقت: {now}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=admin_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    is_new = register_user(update.effective_user)
    if is_new:
        try:
            await notify_new_user(context, update.effective_user)
        except TelegramError as error:
            logger.warning("Could not notify admin: %s", error)
    if not START_IMAGE_PATH.is_file():
        raise RuntimeError(f"ملف صورة البداية غير موجود: {START_IMAGE_PATH}")
    with START_IMAGE_PATH.open("rb") as start_image:
        await update.message.reply_photo(
            photo=start_image,
            caption="اضغط على الزر الموجود على اليسار كما في الصورة.",
        )


async def redirect_to_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        register_user(update.effective_user)
    if update.effective_message:
        await update.effective_message.reply_text("للمتابعة والتسوّق، افتح التطبيق المصغّر من زر البوت.")


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message or update.effective_user.id != ADMIN_ID:
        return
    total, active = stats()
    await update.effective_message.reply_text(
        f"لوحة إدارة كليشة\n\n👥 المستخدمون: {total}\n✅ النشطون في البث: {active}",
        reply_markup=admin_keyboard(),
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query or query.from_user.id != ADMIN_ID:
        return ConversationHandler.END
    await query.answer()
    if query.data == "admin:stats":
        total, active = stats()
        await query.message.reply_text(f"📊 إحصائيات كليشة\n\n👥 كل المستخدمين: {total}\n✅ المستلمون النشطون: {active}")
        return ConversationHandler.END
    if query.data == "broadcast:menu":
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📌 بث مع محاولة تثبيت", callback_data="broadcast:pin")],
                [InlineKeyboardButton("📣 بث عادي", callback_data="broadcast:nopin")],
                [InlineKeyboardButton("✖️ إلغاء", callback_data="broadcast:cancel")],
            ]
        )
        await query.message.reply_text("اختَر نوع البث:", reply_markup=keyboard)
        return ConversationHandler.END
    if query.data == "broadcast:cancel":
        await query.message.reply_text("تم إلغاء البث.")
        return ConversationHandler.END
    if query.data in {"broadcast:pin", "broadcast:nopin"}:
        context.user_data["pin_broadcast"] = query.data == "broadcast:pin"
        await query.message.reply_text("أرسل الآن النص أو الصورة أو الفيديو الذي تريد بثّه.")
        return WAITING_BROADCAST
    return ConversationHandler.END


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.effective_user or update.effective_user.id != ADMIN_ID or not update.effective_message:
        return ConversationHandler.END
    pin = bool(context.user_data.pop("pin_broadcast", False))
    sent = failed = pinned = 0
    status = await update.effective_message.reply_text("بدأ الإرسال…")
    for user_id in active_user_ids():
        try:
            copied = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.effective_message.chat_id,
                message_id=update.effective_message.message_id,
            )
            sent += 1
            if pin:
                try:
                    await context.bot.pin_chat_message(chat_id=user_id, message_id=copied.message_id, disable_notification=True)
                    pinned += 1
                except BadRequest:
                    pass  # التثبيت غير متاح في بعض المحادثات الخاصة.
        except Forbidden:
            mark_inactive(user_id)
            failed += 1
        except TelegramError:
            failed += 1
    await status.edit_text(f"✅ اكتمل البث\n\n📬 تم الإرسال: {sent}\n📌 تم التثبيت حيث يسمح تيليجرام: {pinned}\n🚫 غير متاحين: {failed}")
    return ConversationHandler.END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("pin_broadcast", None)
    if update.effective_message:
        await update.effective_message.reply_text("تم إلغاء وضع البث.")
    return ConversationHandler.END


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("أضف BOT_TOKEN في Variables داخل Railway قبل تشغيل البوت.")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    broadcast_flow = ConversationHandler(
        entry_points=[CallbackQueryHandler(callbacks, pattern=r"^broadcast:(?:pin|nopin)$")],
        states={WAITING_BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast)]},
        fallbacks=[CommandHandler("cancel", cancel_broadcast)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callbacks, pattern=r"^(?:admin:stats|broadcast:menu|broadcast:cancel)$"))
    app.add_handler(broadcast_flow)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, redirect_to_shop))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
