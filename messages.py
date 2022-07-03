from general_functions import get_orders


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
            qr_code = order['qr_code']
            message = f"""
Ваш бокс #{order_id} находится на складе {warehouse_id}. 

Срок хранения: {start_date} - {end_date}. 
QR-код для получения: {qr_code}."""

            return message