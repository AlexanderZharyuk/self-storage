import io
import qrcode
import calendar

from datetime import date, timedelta

from dotenv import load_dotenv
from telegram import (Update, ReplyKeyboardMarkup, KeyboardButton,
                      InlineKeyboardMarkup, InlineKeyboardButton,
                      LabeledPrice)
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, ConversationHandler,
                          CallbackQueryHandler, PreCheckoutQueryHandler)

from messages import *
from general_functions import *
from validate_exceptions import *

USER_FULLNAME, PHONE_NUMBER, END_AUTH, PERSONAL_ACCOUNT, ORDERS, USER_BOXES, CREATE_ORDER = range(7)

SELF_STORAGE_AGREEMENTS: str = 'documents/sample.pdf'

def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user

    if is_new_user(user.id):
        message_keyboard = [['✅ Согласен', '❌ Не согласен']]
        markup = ReplyKeyboardMarkup(message_keyboard, resize_keyboard=True, one_time_keyboard=True)

        with open(SELF_STORAGE_AGREEMENTS, 'rb') as image:
            user_agreement_pdf = image.read()

        greeting_msg = create_start_message_new_user(user.name)
        update.message.reply_document(user_agreement_pdf, filename='Соглашение на обработку персональных данных.pdf',
                                      caption=greeting_msg, reply_markup=markup)

        return USER_FULLNAME
    else:
        message_keyboard = [['Новый заказ', 'Личный кабинет']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)

        menu_msg = create_start_message_exist_user(user.name)
        update.effective_message.reply_text(menu_msg, reply_markup=markup)
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

        database_without_new_user = database_read_users_order()
        database_without_new_user.append(user)
        
        database_write_users_order(database_without_new_user)

        user_data.clear()
        return start(update, context)


def cancel_auth(update: Update, context: CallbackContext) -> None:
    message_keyboard = [['✅ Согласен', '❌ Не согласен']]
    markup = ReplyKeyboardMarkup(message_keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text('Извините, тогда мы не сможем пропустить вас дальше. '
                              'Чтобы изменить решение - напишите /start.', reply_markup=markup)
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
        message_keyboard.append(['Личный кабинет'])
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=False, resize_keyboard=True)
        update.message.reply_text('Выберите заказ', reply_markup=markup)
        return USER_BOXES
    else:
        message_keyboard = [['Главное меню']]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text('Вы еще не оформляли заказов.', reply_markup=markup)
        return ORDERS


def get_box_info(update: Update, context: CallbackContext):
    order_id = update.message.text.split('#')[-1]
    user_id = update.effective_user.id
    info_message = create_info_message(order_id, user_id)

    button = InlineKeyboardButton("QR", callback_data=order_id)
    reply_markup_qr = InlineKeyboardMarkup([[button]])
    update.message.reply_text(info_message, reply_markup=reply_markup_qr)

    return ORDERS


def publish_qr(update: Update, context: CallbackContext):
    query = update.callback_query
    order_id = query.data
    user_id = update.effective_user.id
    info_message = create_info_message_for_qr(order_id, user_id)
    qr_code = make_qr(info_message)
    query.message.reply_photo(qr_code, filename='QR')
    return USER_BOXES


def make_qr(order_info):
    qr_code = qrcode.make(order_info)
    img_byte_arr = io.BytesIO()
    qr_code.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def create_order(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    warehouses_address = get_warehouses_address()
    inline_text = '🏠 Выберите расположение ближайшего для вас склада:\n'
    keyboard = [[]]
    for warehouse in warehouses_address:
           inline_text = inline_text + warehouse['warehouse_id'] + ') ' +  warehouse['warehouse_address'] + '\n'
           keyboard[0].append(InlineKeyboardButton(warehouse['warehouse_id'], callback_data=str('warehouse_id:' + warehouse['warehouse_id'])))
    inline_markup = InlineKeyboardMarkup(keyboard)

    if query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=inline_text, reply_markup=inline_markup)
    else:
        msg_text = ('📝 Оформление заказа:')
        message_keyboard = [
            [
                KeyboardButton('⬅️ Вернуться в главное меню'),
                KeyboardButton('📍 Ближайший склад', request_location=True)
            ]
        ]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=False, resize_keyboard=True)
        update.effective_message.reply_text(msg_text, reply_markup=markup)

        update.effective_message.reply_text(text=inline_text, reply_markup=inline_markup)
    return CREATE_ORDER
    

def create_order_steps(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    key, id = query.data.split(':')
    context.user_data[key] = id
    if key == 'warehouse_id':
        msg_text = create_order_info_messgaes(key, context.user_data)
        keyboard = [
            [
                InlineKeyboardButton("3 м2", callback_data=str('box_size:0')),
                InlineKeyboardButton("10 м2", callback_data=str('box_size:1')),
                InlineKeyboardButton("более 10 м2", callback_data=str('box_size:2'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
            
    elif key == 'box_size':
        msg_text = create_order_info_messgaes(key, context.user_data)
        keyboard = [
            [
                InlineKeyboardButton("Нет ❌", callback_data=str('box_type:0')),
                InlineKeyboardButton("Да ✅", callback_data=str('box_type:1'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    elif key == 'box_type':
        msg_header = create_order_info_messgaes(key, context.user_data)
        boxes_list = get_warehouses_boxes(context.user_data)
        msg_boxes_list = create_boxes_list_message(boxes_list)
        msg_text= "".join([msg_header, msg_boxes_list]) 
        keyboard = [
            []
        ]
        
        for box in boxes_list:
            keyboard[0].append(InlineKeyboardButton(box['box_id'], callback_data=str('box_id:' + box['box_id'])),)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
        
        if not boxes_list:
            context.user_data.clear()
 
    elif key == 'box_id':
        context.user_data['box_floor'] = get_box_floor(context.user_data)
        context.user_data['box_price'] = get_box_price(context.user_data)
        msg_text = create_order_info_messgaes(key, context.user_data)
        keyboard = [
                    [
                        InlineKeyboardButton("1", callback_data=str('order_time:1')),
                        InlineKeyboardButton("3", callback_data=str('order_time:3')),
                        InlineKeyboardButton("6", callback_data=str('order_time:6')),
                        InlineKeyboardButton("12", callback_data=str('order_time:12')),
                    ]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)

    elif key == 'order_time':
        today = date.today()
        days = calendar.monthrange(today.year, today.month)[1]
        end_date = today + timedelta(days=days * int(id))
        context.user_data['start_date'] = "{}/{}/{}".format(today.year, today.month, today.day)
        context.user_data['end_date'] = "{}/{}/{}".format(end_date.year, end_date.month, end_date.day)

        msg_text = create_order_info_messgaes(key, context.user_data)
        keyboard = [
                    [
                        InlineKeyboardButton("Изменить", callback_data=str('change_order:1')),
                        InlineKeyboardButton("Подтвердить", callback_data=str('order_make_payment:1')),
                    ]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    elif key == 'change_order':
        context.user_data.clear()
        create_order(update, context)
        
    elif key == 'order_make_payment':
        start_without_shipping_callback(query, context)
        return PERSONAL_ACCOUNT
    return CREATE_ORDER


def location(update: Update, context: CallbackContext):
    user_pos = (update.message.location.latitude, update.message.location.longitude)
    warehouses_location = get_warehouses_location(user_pos)

    inline_text = f"🏠 Ближайший до вас склад:\n\n{warehouses_location['warehouse_address']}"
    keyboard = [
        [
            InlineKeyboardButton("Изменить", callback_data=str('change_warehouse')),
            InlineKeyboardButton("Выбрать", callback_data=str('warehouse_id:' + warehouses_location['warehouse_id'])),
        ]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text(text=inline_text, reply_markup=inline_markup)
    return CREATE_ORDER


def start_without_shipping_callback(update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    strings = [string.strip() for string in update.message.text.split('\n')]

    box_number = None
    summary = None
    for string in strings:
        if string.startswith('#️⃣ Номер'):
            box_number = string[string.find(':') + 2:]
        if string.startswith('💰 Стоимость'):
            start_index = string.find(':') + 1
            end_index = string.find('RUB')
            summary = int(string[start_index:end_index].strip(' '))

    title = "Аренда бокса"
    description = f"Аренда бокса #{box_number}"
    payload = "BOT Payment"
    provider_token = os.environ['PAYMENT_TOKEN']
    currency = "RUB"
    price = 100
    prices = [LabeledPrice(f"Бокс {box_number}", price * summary)]

    context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        start_parameter='12345',
        currency=currency,
        prices=prices,
        need_name=False,
        need_phone_number=False,
        need_email=True,
        is_flexible=False,
    )


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload != 'BOT Payment':
        query.answer(ok=False, error_message="С оформлением заказа произошла ошибка.")
    else:
        query.answer(ok=True)


def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    msg_text = create_order_info_messgaes('order_make_payment', context.user_data)
    update.message.reply_text(msg_text)
    
    user_id = update.effective_user.id
    add_new_user_order(user_id, context.user_data)
    context.user_data.clear()
    start(update, context)


if __name__ == '__main__':
    load_dotenv()
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']

    database_create_users_order()

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
                    Filters.regex('^(Новый заказ)$'), create_order
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
                MessageHandler(
                    Filters.regex('^(Личный кабинет)$'), personal_account
                ),
                MessageHandler(
                    Filters.regex(r'Заказ #'), get_box_info
                ),
                CallbackQueryHandler(publish_qr)
            ],
            USER_BOXES: [
                MessageHandler(
                    Filters.regex(r'Заказ #'), get_box_info
                ),
                MessageHandler(
                    Filters.regex('^(Личный кабинет)$'), personal_account
                ),
            ],
            CREATE_ORDER: [
                MessageHandler(
                    Filters.regex('^(⬅️ Вернуться в главное меню)$'), start
                ),
                MessageHandler(
                    Filters.location, location
                ),
                CallbackQueryHandler(create_order, pattern='^' + 'change_warehouse' + '$'),
                CallbackQueryHandler(create_order_steps),
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Стоп$'), start)],
    )

    dispatcher.add_handler(MessageHandler(Filters.regex('^❌ Не согласен$'), cancel_auth))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
    dispatcher.add_handler(CallbackQueryHandler(successful_payment_callback))

    updater.start_polling()
    updater.idle()
