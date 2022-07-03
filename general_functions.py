import json

from string import ascii_letters, digits

from validate_exceptions import *


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


def clear_phone_number(phone_number: str) -> str:
    """Функция очищает номер телефона от лишних симоволов"""
    numbers_in_phone = [number for number in phone_number if number in digits]
    phone_without_symbols = "".join(numbers_in_phone)
    if phone_without_symbols.startswith('7'):
        return f'+{phone_without_symbols}'
    else:
        raise NotCorrectStartNumber


def is_valid_phone_number(phone_number: str) -> bool:
    """Проверка на валидность номера телефона"""
    cleared_phone_number = clear_phone_number(phone_number)

    if len(cleared_phone_number) > 12:
        raise NumberLengthTooLong
    elif len(cleared_phone_number) < 12:
        raise NumberLengthTooShort

    return True


def is_fullname_valid(fullname: list) -> bool:
    """Проверка на валидность имени и фамилии"""
    if len(fullname) < 2:
        raise NotFullName

    for digit in digits:
        if str(digit) in ' '.join(fullname):
            raise DigitsInName

    return True
