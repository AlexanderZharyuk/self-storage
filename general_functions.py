import json

from string import ascii_letters, digits

from validate_exceptions import *

import random

def is_new_user(user_id: int) -> bool:
    """Функция возвращает True или False в зависимости от того - есть ли пользователь в базе данных"""
    with open('json_files/users_order.json', 'r', encoding="utf-8") as file:
        users = json.load(file)

    users_ids = [user['user_id'] for user in users if user['user_id'] == user_id]
    return not bool(users_ids)


def get_orders(user_id: int) -> list:
    """Функция для получения списка заказов пользователя"""
    with open('json_files/users_order.json', 'r', encoding="utf-8") as file:
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


def get_warehouse_address(warehouse_id):
    """Функция для получения адреса по номеру склада"""
    with open('json_files/warehouses.json', 'r', encoding="utf-8") as file:
        warehouses = json.load(file)
        for warehouse in warehouses:
            if warehouse_id == warehouse['warehouse_id']:
                address = warehouse['warehouse_address']
                return address


def get_warehouses_address() -> list:
    """Функция для получения списка адресов складов"""
    with open('json_files/warehouses.json', 'r', encoding='utf-8') as json_file:
        warehouses = json.load(json_file)
    warehouses_address = [dict({'warehouse_id': warehouse['warehouse_id'], 'warehouse_address': warehouse['warehouse_address']}) for warehouse in warehouses]
    return warehouses_address

    
def get_warehouses_boxes(params_by_user: dict) -> list:
    """Функция для получения списка всех доступных боксов с указаннными пользователем параметрами на складе"""
    with open('json_files/warehouses.json', 'r', encoding='utf-8') as json_file:
        warehouses = json.load(json_file)
    boxes = []

    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if (box['box_size'] == params_by_user['box_size'] and 
                box['box_type'] == params_by_user['box_type'] and 
                not box['box_reserved']):
                boxes.append(box)
    return boxes


def get_box_floor(params_by_user: dict) -> list:
    """Функция для получения этажа на котором находится выбранный бокс"""
    with open('json_files/warehouses.json', 'r', encoding='utf-8') as json_file:
        warehouses = json.load(json_file)

    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if box['box_id'] == params_by_user['box_id']:
                return box['box_floor']


def add_new_user_order(user_id: int, order_params: dict):
    """Функция добавления нового заказа в базу"""
    with open('json_files/users_order.json', 'r', encoding="utf-8") as json_file:
            users = json.load(json_file)

    for user in users:
        if (user['user_id'] == user_id):
            new_order = {
                "order_id": random.randint(1,200),
                "qr_code": "1",
                "warehouse_id": order_params['warehouse_id'],
                "box_id": order_params['box_id'],
                "start_date": order_params['start_date'],
                "end_date": order_params['end_date'],
                }
            user['orders'].append(new_order)

    with open('json_files/users_order.json', 'w', encoding="utf-8") as json_file:
        json.dump(users, json_file, indent=4, ensure_ascii=False)
