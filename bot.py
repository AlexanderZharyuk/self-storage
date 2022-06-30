import os
import json

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, CallbackQueryHandler,
                          ConversationHandler)

from messages import create_start_message
from general_functions import is_new_user

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['👤 Имя и Фамилия', '📱 Номер телефона'],
    ['Зарегистрироваться'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data) -> str:
    facts = [f'{key} - {value}' for key, value in user_data.items()]

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user

    if is_new_user(user.id):
        message_keyboard = [[
            InlineKeyboardButton('✅ Согласен', callback_data='agree_user_agreement')
        ]]
        reply_markup = InlineKeyboardMarkup(message_keyboard)

        with open('documents/sample.pdf', 'rb') as image:
            user_agreement_pdf = image.read()

        greeting_msg = create_start_message(user.name)
        update.message.reply_document(user_agreement_pdf, filename='Соглашение на обработку персональных данных.pdf',
                                      caption=greeting_msg, reply_markup=reply_markup)

        return CHOOSING


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'agree_user_agreement':
        query.message.reply_text("Выберите опцию, которую хотите указать", reply_markup=markup)


def regular_choice(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'{text.lower()}?')

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Заполненные данные:"
        f"{facts_to_str(user_data)}",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data

    if 'choice' in user_data:
        del user_data['choice']

    if len(user_data) < 2:
        update.message.reply_text('Вы указали не все данные для регистрации, попробуйте снова.')
        return CHOOSING
    else:
        user_fullname = user_data['👤 Имя и Фамилия'].split()
        if len(user_fullname) < 2:
            update.message.reply_text('Вы не указали имя или фамилию, попробуйте снова.')
            return CHOOSING

        user_phone_number = user_data['📱 Номер телефона']
        user_id = update.effective_user.id

        user = {
            "user_id": user_id,
            "first_name": user_fullname[0],
            "last_name": user_fullname[1],
            "phone_number": user_phone_number,
            "orders": []
        }

        with open('json_files/users_order.json', 'r') as json_file:
            database_without_new_user = json.load(json_file)

        database_without_new_user.append(user)

        with open('json_files/users_order.json', 'w') as json_file:
            json.dump(database_without_new_user, json_file, indent=4, ensure_ascii=False)

        update.message.reply_text(
            f"Аккаунт создан!",
            reply_markup=ReplyKeyboardRemove(),
        )

        user_data.clear()
        return ConversationHandler.END


if __name__ == '__main__':
    load_dotenv()
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(👤 Имя и Фамилия|📱 Номер телефона)$'), regular_choice
                ),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Зарегистрироваться$')), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Зарегистрироваться$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Зарегистрироваться$'), done)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()
