import os
import json

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, CallbackQueryHandler,
                          ConversationHandler)

from messages import create_start_message_new_user, create_start_message_exist_user
from general_functions import is_new_user

USER_FULLNAME, PHONE_NUMBER, END_AUTH = range(3)


def facts_to_str(user_data) -> str:
    facts = [f'{key} - {value}' for key, value in user_data.items()]

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user

    if is_new_user(user.id):
        message_keyboard = [['✅ Согласен', '❌ Не согласен']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)

        with open('documents/sample.pdf', 'rb') as image:
            user_agreement_pdf = image.read()

        greeting_msg = create_start_message_new_user(user.name)
        update.message.reply_document(user_agreement_pdf, filename='Соглашение на обработку персональных данных.pdf',
                                      caption=greeting_msg, reply_markup=markup)

        return USER_FULLNAME
    else:
        message_keyboard = [['Заказ', 'Личный кабинет']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)

        menu_msg = create_start_message_exist_user(user.name)
        update.message.reply_text(menu_msg, reply_markup=markup)


def get_fullname(update: Update, context: CallbackContext) -> int:
    context.user_data['choice'] = 'Имя и фамилия'
    update.message.reply_text(f'Введите имя и фамилию:')

    return PHONE_NUMBER


def get_phone_number(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    context.user_data['choice'] = 'Телефон'
    update.message.reply_text(f'Введите телефон:')

    return END_AUTH


def end_auth(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text

    if 'choice' in user_data:
        del user_data['choice']

        user_fullname = user_data['Имя и фамилия'].split()
        if len(user_fullname) < 2:
            update.message.reply_text('Вы ввели не указали фамилию или имя, попробуйте снова.')
            return USER_FULLNAME

        user_phone_number = user_data['Телефон']
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

        message_keyboard = [['Заказ', 'Личный кабинет']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)

        update.message.reply_text(
            f"Аккаунт создан!\n"
            f"Выберите, что хотите сделать:",
            reply_markup=markup,
        )

        user_data.clear()
        return ConversationHandler.END


def cancel_auth(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Извините, тогда мы не сможем пропустить вас дальше')


if __name__ == '__main__':
    load_dotenv()
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USER_FULLNAME: [
                MessageHandler(
                    Filters.regex('^(✅ Согласен)$'), get_fullname
                ),
            ],
            PHONE_NUMBER: [
                MessageHandler(
                    Filters.text, get_phone_number
                )
            ],
            END_AUTH: [
                MessageHandler(
                    Filters.text, end_auth
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Стоп$'), start)],
    )

    dispatcher.add_handler(MessageHandler(Filters.regex('^❌ Не согласен$'), cancel_auth))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()
