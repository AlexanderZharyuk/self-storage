import os
import textwrap

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from messages import create_start_message


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    greeting_msg = create_start_message(user.name)

    update.message.reply_text(greeting_msg)


if __name__ == '__main__':
    load_dotenv()
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()
