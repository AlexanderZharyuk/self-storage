import io
import os
import json
import qrcode
import calendar
from datetime import date, timedelta

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, ConversationHandler,
                          CallbackQueryHandler)

from messages import create_start_message_new_user, create_start_message_exist_user, create_info_message, create_info_message_for_qr, create_boxes_list_message, create_show_user_order_message
from general_functions import is_new_user, get_orders_ids, is_valid_phone_number, is_fullname_valid, clear_phone_number, get_warehouses_address, get_warehouses_boxes, get_box_floor, add_new_user_order
from validate_exceptions import *

USER_FULLNAME, PHONE_NUMBER, END_AUTH, PERSONAL_ACCOUNT, ORDERS, USER_BOXES, CREATE_ORDER = range(7)


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
    message_keyboard = [[KeyboardButton('Отправить свой номер телефона', request_contact=True)]]
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
    except NumberLengthTooShort:
        update.message.reply_text('Длина телефона слишком мала.')
        return get_phone_number(update, context)
    except NumberLengthTooLong:
        update.message.reply_text('Длина телефона слишком большая.')
        return get_phone_number(update, context)
    except NotCorrectStartNumber:
        update.message.reply_text('Номер начинается не на +7...')
        return get_phone_number(update, context)

    category = user_data['choice']
    user_data[category] = text

    if 'choice' in user_data:
        del user_data['choice']

        user_fullname = user_data['Имя и фамилия'].split()
        user_phone_number = clear_phone_number(user_data['Телефон'])
        user_id = update.effective_user.id

        user = {
            "user_id": user_id,
            "first_name": user_fullname[0],
            "last_name": user_fullname[1],
            "phone_number": user_phone_number,
            "orders": []
        }

        with open('json_files/users_order.json', 'r', encoding="utf-8") as json_file:
            database_without_new_user = json.load(json_file)

        database_without_new_user.append(user)

        with open('json_files/users_order.json', 'w', encoding="utf-8") as json_file:
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
    info_message = create_info_message_for_qr(order_id, user_id)
    qr_code = make_qr(info_message)
    query.message.reply_photo(qr_code, filename='QR')


def make_qr(order_info):
    qr_code = qrcode.make(order_info)
    img_byte_arr = io.BytesIO()
    qr_code.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def order_select_warehouse(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query:
        query.answer()

    warehouses_address = get_warehouses_address()
    msg_text = '🏠 Выберите расположение ближайшего для вас склада:\n'
    keyboard = [[]]
    for warehouse in warehouses_address:
           msg_text = msg_text + warehouse['warehouse_id'] + ') ' +  warehouse['warehouse_address'] + '\n'
           keyboard[0].append(InlineKeyboardButton(warehouse['warehouse_id'], callback_data=str('warehouse_id:' + warehouse['warehouse_id'])),)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    else:
        update.message.reply_text(msg_text, reply_markup=reply_markup)
    
    return CREATE_ORDER

def order_create(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    object, id = query.data.split(':')
    context.user_data[object] = id

    if object=='warehouse_id':
        msg_text = 'Выберите необходимый размер бокса:\n'
        keyboard = [
            [
                InlineKeyboardButton("3 м2", callback_data=str('box_size:0')),
                InlineKeyboardButton("10 м2", callback_data=str('box_size:1')),
                InlineKeyboardButton("более 10 м2", callback_data=str('box_size:2'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    elif object=='box_size':
        msg_text = 'Вы собираетесь хранить специфические вещи (различные легковоспоменяющиеся жидкости, крупногабаритные и т.п.)?\n'
        keyboard = [
                    [
                        InlineKeyboardButton("Нет ❌", callback_data=str('box_type:0')),
                        InlineKeyboardButton("Да ✅", callback_data=str('box_type:1'))
                    ]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    elif object=='box_type':
        boxes = get_warehouses_boxes(context.user_data)
        msg_text = create_boxes_list_message(boxes)
        keyboard = [[]]
        for box in boxes:
            keyboard[0].append(InlineKeyboardButton(box['box_id'], callback_data=str('box_id:' + box['box_id'])),)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
        if not boxes:
            context.user_data.clear()
            return PERSONAL_ACCOUNT
    
    elif object=='box_id':
        context.user_data['box_floor'] = get_box_floor(context.user_data)
        msg_text = '⏱️ На какой срок вы хотите арендовать бокс?\n'
        keyboard = [
                    [
                        InlineKeyboardButton("1 месяц", callback_data=str('order_time:1')),
                        InlineKeyboardButton("3 месяца", callback_data=str('order_time:3')),
                        InlineKeyboardButton("6 месяцев", callback_data=str('order_time:6')),
                        InlineKeyboardButton("12 месяцев", callback_data=str('order_time:12')),
                    ]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)

    elif object=='order_time':
        today = date.today()
        days = calendar.monthrange(today.year, today.month)[1]
        end_date = today + timedelta(days=days * int(id))
        context.user_data['start_date'] = "{}/{}/{}".format(today.year, today.month, today.day)
        context.user_data['end_date'] = "{}/{}/{}".format(end_date.year, end_date.month, end_date.day)
    
        msg_text = create_show_user_order_message(context.user_data)
        keyboard = [
                    [
                        InlineKeyboardButton("Изменить", callback_data=str('change_order:1')),
                        InlineKeyboardButton("Подтвердить", callback_data=str('order_make_payment:1')),
                    ]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    elif object=='change_order':
        context.user_data.clear()
        order_select_warehouse(update, context)

    elif object=='order_make_payment':
        query.message.reply_text('Ваш заказ принят.\nВ ближайшее время с вами свяжется менеджер 📞\nСпасибо, что доверяете нам свои вещи!')
        #
        # Code for order payment
        #

        # Save payment order to json
        user_id = update.effective_user.id
        add_new_user_order(user_id, context.user_data)
        context.user_data.clear()
        return PERSONAL_ACCOUNT
    return CREATE_ORDER

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
                    Filters.regex('^(Заказ)$'), order_select_warehouse
                ),
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
            ],
            CREATE_ORDER: [
                CallbackQueryHandler(order_create)
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
