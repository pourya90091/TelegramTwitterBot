import os
import asyncio
from pathlib import Path

from telegram import (
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    AIORateLimiter,
    filters
)
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode, ChatAction
from dotenv import load_dotenv
from core import initialize, comment, logger
import database
from functools import wraps
from pathlib import Path


load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = os.getenv("ADMINS")


def admin_check(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        update = args[0]
        username = update.message.from_user.username
        if username in ADMINS.split(", "):
            return await func(*args, **kwargs)
        await update.message.reply_text("You are not authorized", parse_mode=ParseMode.HTML)
    return wrapper


@admin_check
async def start_handle(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"""
Hey @{update.message.from_user.username}, i'm here to help you out.
                                    
My commands:
    /select
    /export
        """, parse_mode=ParseMode.HTML)


@admin_check
async def select_handle(update: Update, context: CallbackContext) -> None:
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("DailyMonitor", callback_data="DailyMonitor"),
        ],
        [
            InlineKeyboardButton("BBCWorld", callback_data="BBCWorld"),
        ],
        [
            InlineKeyboardButton("Entekhab_News", callback_data="Entekhab_News")
        ]
    ])

    await update.message.reply_text("Please choose an account:", reply_markup=reply_markup)


@admin_check
async def export_handle(update: Update, context: CallbackContext) -> None:
    file_name = database.export_all_replies()

    await update.message.reply_document(document=open(f"{BASE_DIR}/{file_name}", "rb"))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and calls core.comment() function."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat_id, text=f"Action begins for @{query.data}")
    result = await comment(query.data)

    if "Error occurred" in result:
        await context.bot.send_message(chat_id=query.message.chat_id, text=result)
        return None

    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Reply URL", url=result),
        ]
    ])
    await context.bot.send_message(chat_id=query.message.chat_id, text=f"Reply URL:", reply_markup=reply_markup)


def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .build()
    )

    # add handlers
    application.add_handler(CommandHandler("start", start_handle))
    application.add_handler(CommandHandler("select", select_handle))
    application.add_handler(CommandHandler("export", export_handle))
    application.add_handler(CallbackQueryHandler(button))

    # start the bot
    logger.info("Bot has been started.")

    application.run_polling()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    database.init()
    loop.run_until_complete(initialize())

    run_bot()
