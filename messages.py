from general_functions import get_orders, get_warehouse_address


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
