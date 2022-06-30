import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from messages import create_start_message


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message_keyboard = [[
        InlineKeyboardButton('✅ Согласен', callback_data='agree_user_agreement')
    ]]
    reply_markup = InlineKeyboardMarkup(message_keyboard)

    with open('documents/sample.pdf', 'rb') as image:
        user_agreement_pdf = image.read()

    greeting_msg = create_start_message(user.name)
    update.message.reply_document(user_agreement_pdf, filename='Соглашение на обработку персональных данных.pdf',
                                  caption=greeting_msg, reply_markup=reply_markup)


if __name__ == '__main__':
    load_dotenv()
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()
