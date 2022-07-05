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
            boxes_list_msg = boxes_list_msg + f"""\n
    📦 Бокс для хранения #{box['box_id']}
    🎢 Этаж: {box['box_floor']}
    📏 Размер: {box['box_size']}
    💰 Стоимость: {box['box_price']}
    """
    return boxes_list_msg


def create_show_user_order_message(order: dict) -> str:
    """Здесь написан текст для показа заказа пользователя на этапе его формирования для подтверждения перед оплатой"""
    with open('json_files/warehouses.json', 'r') as file:
        warehouses = json.load(file)

    for warehouse in warehouses:
        if warehouse['warehouse_id'] == order['warehouse_id']:
            founded_box = [box for box in warehouse['boxes'] if box['box_id'] == order['box_id']][0]

            start_rent_date = datetime.strptime(order['start_date'], '%Y/%m/%d')
            end_rent_date = datetime.strptime(order['end_date'], '%Y/%m/%d')
            rent_months = (end_rent_date - start_rent_date).days // 30
            rent_price = int(founded_box['box_price']) * rent_months

    user_order = '📝 Проверьте и подтвердите ваш заказ:'
    user_order = user_order + f"""\n
    📦 Бокс для хранения #{order['box_id']}
    🎢 Этаж: {order['box_floor']}
    📏 Размер: {order['box_size']}
    💰 Срок аренды: {order['end_date']}
    💸 Стоимость аренды: {rent_price} RUB
    """
    return user_order