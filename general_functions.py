import json


def is_new_user(user_id: int) -> bool:
    """Функция возвращает True или False в зависимости от того - есть ли пользователь в базе данных"""
    with open('json_files/users_order.json', 'r') as file:
        users = json.load(file)

    users_ids = [user['user_id'] for user in users if user['user_id'] == user_id]
    return not bool(users_ids)


def get_orders(user_id: int) -> list:
    """Функция для получения списка заказов пользователя"""
    with open('json_files/users_order.json', 'r') as file:
        users = json.load(file)
    user_orders = [user['orders'] for user in users if user['user_id'] == user_id]
    return user_orders


def get_orders_ids(user_id: int) -> list:
    """Функция получения айди всех заказов пользователя"""
    orders = get_orders(user_id)[0]
    user_orders_id = [order['order_id'] for order in orders]
    return user_orders_id
