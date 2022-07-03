import io
import os
import json
import qrcode

from string import digits, ascii_letters

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, ConversationHandler,
                          CallbackQueryHandler)

from messages import create_start_message_new_user, create_start_message_exist_user, create_info_message
from general_functions import is_new_user, get_orders_ids, is_valid_phone_number, is_fullname_valid
from validate_exceptions import *

USER_FULLNAME, PHONE_NUMBER, END_AUTH, PERSONAL_ACCOUNT, ORDERS, USER_BOXES = range(6)


def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user

    if is_new_user(user.id):
        message_keyboard = [['✅ Согласен', '❌ Не согласен']]
        markup = ReplyKeyboardMarkup(message_keyboard, resize_keyboard=True)

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

        return PERSONAL_ACCOUNT


def get_fullname(update: Update, context: CallbackContext) -> int:
    context.user_data['choice'] = 'Имя и фамилия'
    update.message.reply_text(f'Введите имя и фамилию:')

    return PHONE_NUMBER


def get_phone_number(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    user_fullname = user_data['Имя и фамилия'].split()
    try:
        is_fullname_valid(user_fullname)
    except NotFullName:
        update.message.reply_text('Вы не указали фамилию или имя, попробуйте снова.')
        return get_fullname(update, context)
    except DigitsInName:
        update.message.reply_text('В имени или фамилии присутствуют цифры!')
        return get_fullname(update, context)

    context.user_data['choice'] = 'Телефон'
    message_keyboard = [[KeyboardButton('Поделиться контактом', request_contact=True)]]
    markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(f'Введите телефон в формате +7... или нажав на кнопку ниже:', reply_markup=markup)

    return END_AUTH


def end_auth(update: Update, context: CallbackContext):
    user_data = context.user_data
    if update.message.contact:
        text = update.message.contact.phone_number
    else:
        text = update.message.text

    try:
        is_valid_phone_number(text)
    except LetterInNumber:
        update.message.reply_text('В вашем телефоне найден запрещенный символ.')
        return get_phone_number(update, context)
    except NumberLength:
        update.message.reply_text('Длина телефона слишком мала.')
        return get_phone_number(update, context)

    category = user_data['choice']
    user_data[category] = text

    if 'choice' in user_data:
        del user_data['choice']

        user_fullname = user_data['Имя и фамилия'].split()
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

        user_data.clear()
        return start(update, context)


def cancel_auth(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Извините, тогда мы не сможем пропустить вас дальше. '
                              'Чтобы изменить решение - напишите /start.')
    return ConversationHandler.END


def personal_account(update: Update, context: CallbackContext):
    message_keyboard = [['Посмотреть заказы', 'Главное меню']]
    markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True,
                                 resize_keyboard=True)
    update.message.reply_text('Выберите, что хотите сделать:', reply_markup=markup)
    return ORDERS


def get_orders_list(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    orders_ids = get_orders_ids(user_id)
    if orders_ids:
        message_keyboard = [[f'Заказ #{order_id}'] for order_id in orders_ids]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text('Выберите заказ', reply_markup=markup)
        return USER_BOXES
    else:
        message_keyboard = [['Выйти из личного кабинета']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text('Вы еще не оформляли заказов.', reply_markup=markup)
        return ORDERS


def get_box_info(update: Update, context: CallbackContext):
    message_keyboard = [['Вернуться к заказам', 'Главное меню']]
    markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)
    order_id = update.message.text.split('#')[-1]
    user_id = update.effective_user.id
    info_message = create_info_message(order_id, user_id)
    update.message.reply_text(info_message, reply_markup=markup)

    button = InlineKeyboardButton("QR", callback_data=order_id)
    reply_markup_qr = InlineKeyboardMarkup([[button]])
    update.message.reply_text('Нажмите, чтобы получить QR-code', reply_markup=reply_markup_qr)

    return ORDERS


def publish_qr(update: Update, context: CallbackContext):
    query = update.callback_query
    order_id = query.data
    user_id = update.effective_user.id
    info_message = create_info_message(order_id, user_id)
    qr_code = make_qr(info_message)
    query.message.reply_photo(qr_code, filename='QR')


def make_qr(order_info):
    qr_code = qrcode.make(order_info)
    img_byte_arr = io.BytesIO()
    qr_code.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


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
                ),
                MessageHandler(
                    Filters.contact, end_auth
                )
            ],
            PERSONAL_ACCOUNT: [
                MessageHandler(
                    Filters.regex('^(Личный кабинет)$'), personal_account
                )
            ],
            ORDERS: [
                MessageHandler(
                    Filters.regex('^(Посмотреть заказы)$'), get_orders_list
                ),
                MessageHandler(
                    Filters.regex('^(Главное меню)$'), start
                ),
                MessageHandler(
                    Filters.regex('^(Вернуться к заказам)$'), get_orders_list
                ),
            ],
            USER_BOXES: [
                MessageHandler(
                    Filters.regex(r'Заказ #'), get_box_info
                ),
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Стоп$'), start)],
    )

    dispatcher.add_handler(MessageHandler(Filters.regex('^❌ Не согласен$'), cancel_auth))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(publish_qr))

    updater.start_polling()
    updater.idle()
