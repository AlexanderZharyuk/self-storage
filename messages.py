from ast import If
import json

from general_functions import get_orders, get_warehouse_address

from datetime import datetime


def create_start_message_new_user(username: str) -> str:
    """Здесь написан текст стартового сообщения для нового пользователя"""
    greeting_msg = f"""
Привет, {username}!
    
Self-storage - бот по аренде складского помещения.
Если вам интересны наши услуги, пожалуйста, пройдите регистрацию.

Для этого согласитесь на обработку персональных данных.
"""

    return greeting_msg


def create_start_message_exist_user(username: str) -> str:
    """Здесь написан текст стартового сообщения для существующего пользователя"""
    greeting_msg = f"""
Привет, {username}!

Self-storage - бот по аренде складского помещения.
Выберите, куда хотите перейти. 
"""
    return greeting_msg


def create_info_message(order_id, user_id):
    """Здесь создается сообщение с информацией о боксе"""
    orders = get_orders(user_id)[0]
    for order in orders:
        if int(order_id) == order['order_id']:
            warehouse_id = order['warehouse_id']
            start_date = order['start_date']
            end_date = order['end_date']
            box_id = order['box_id']
            address = get_warehouse_address(warehouse_id)
            message = f"""
❗️ Ваш заказ #{order_id}
📦 Бокс #{box_id} 
🏚 Cклад #{warehouse_id} 
🗺 Адрес {address}. 

🕔 Срок хранения: 
{start_date} - {end_date}"""

            return message


def create_info_message_for_qr(order_id, user_id):
    """Здесь создается сообщение с информацией о боксе для формирования qr-code"""
    orders = get_orders(user_id)[0]
    for order in orders:
        if int(order_id) == order['order_id']:
            warehouse_id = order['warehouse_id']
            start_date = order['start_date']
            end_date = order['end_date']
            box_id = order['box_id']
            message = f"""
            Order id: {order_id}
            Box id: {box_id}
            Warehouse id: {warehouse_id}
            Start date: {start_date}
            End date: {end_date}"""

            return message


def create_boxes_list_message(boxes: list) -> str:
    """Здесь написан текст для списка свободных боксов"""
    if not boxes:
        boxes_list_msg = "В данный момент на этом складе нет свободных боксов удовлетворяющих вашему запросу."    
    else:
        boxes_list_msg = "Список доступных боксов:"
        for box in boxes:
            boxes_list_msg = boxes_list_msg + f"""
    📦 Бокс для хранения #{box['box_id']}
    🎢 Этаж: {box['box_floor']}
    📏 Размер: {box['box_size']}
    💰 Стоимость: {box['box_price']} RUB

    """
    return boxes_list_msg


def create_order_info_messgaes(key: str, user_data: dict) -> str:
    """Создание информационного сообщения в процессе формирования заказа"""
    if key == 'warehouse_id':
        info_msg = f"""
🏠 Адрес: {get_warehouse_address(user_data['warehouse_id'])}

Выберите необходимый размер бокса:
"""

    if key == 'box_size':
        info_msg = f"""
🏠 Адрес: {get_warehouse_address(user_data['warehouse_id'])}
📏 Размер бокса: {user_data['box_size']}

Вы собираетесь хранить специфические вещи (различные легковоспоменяющиеся жидкости, крупногабаритные и т.п.)?\n
"""

    if key == 'box_type':
        info_msg = f"""
🏠 Адрес: {get_warehouse_address(user_data['warehouse_id'])}
📏 Размер бокса: {user_data['box_size']}
☢ Специфичный бокс: {user_data['box_type']}

"""

    if key == 'box_id':
        info_msg = f"""
🏠 Адрес: {get_warehouse_address(user_data['warehouse_id'])}
📏 Размер бокса: {user_data['box_size']}
☢ Специфичный бокс: {user_data['box_type']}
#️⃣ Номер бокса: {user_data['box_id']}
🎢 Этаж: {user_data['box_floor']}
💰 Стоимость: {user_data['box_price']} RUB

⏱️ На сколько месяцев вы хотите арендовать бокс?
"""

    if key == 'order_time' or key == 'order_make_payment':
        if key == 'order_time':
            user_data['rent_price'] = int(user_data['box_price']) * int(user_data['order_time'])
            info_msg = f"""
🏠 Адрес: {get_warehouse_address(user_data['warehouse_id'])}
📏 Размер бокса: {user_data['box_size']}
☢ Специфичный бокс: {user_data['box_type']}
#️⃣ Номер бокса: {user_data['box_id']}
🎢 Этаж: {user_data['box_floor']}
⏱️ Срок аренды: {user_data['end_date']}
💰 Стоимость аренды: {user_data['rent_price']} RUB

📝 Всё верно?
"""
        else:
            info_msg = '✅ Ваш заказ принят\n📞 В ближайшее время с вами свяжется менеджер' \
                       '\n🤝 Спасибо, что доверили нам свои вещи!'

    return info_msg
