import os
import json
import random

from string import digits
from geopy import distance

from validate_exceptions import *

SELF_STORAGE_DATABASE_USERS_ORDER: str = 'json_files/users_order.json'
SELF_STORAGE_DATABASE_WAREHOUSE: str = 'json_files/warehouses.json'

def database_read_from_file(database_path: str) -> list: 
    with open(database_path, 'r', encoding="utf-8") as file:
        return json.load(file)

def database_write_to_file(database_path: str, items: list) -> list: 
    with open(database_path, 'w', encoding="utf-8") as json_file:
        json.dump(items, json_file, indent=4, ensure_ascii=False)


def database_read_users_order() -> list: 
    return database_read_from_file(SELF_STORAGE_DATABASE_USERS_ORDER)


def database_write_users_order(items: list) -> list: 
    return database_write_to_file(SELF_STORAGE_DATABASE_USERS_ORDER, items)


def database_read_warehouses() -> list: 
    return database_read_from_file(SELF_STORAGE_DATABASE_WAREHOUSE)


def database_write_warehouses(items: list) -> list: 
    return database_write_to_file(SELF_STORAGE_DATABASE_WAREHOUSE, items)


def database_create_users_order():
    if not os.path.exists(SELF_STORAGE_DATABASE_USERS_ORDER):
        os.makedirs('json_files', exist_ok=True)
        database_write_users_order([])


def is_new_user(user_id: int) -> bool:
    """Функция возвращает True или False в зависимости от того - есть ли пользователь в базе данных"""
    users = database_read_users_order()
    users_ids = [user['user_id'] for user in users if user['user_id'] == user_id]
    return not bool(users_ids)


def get_orders(user_id: int) -> list:
    """Функция для получения списка заказов пользователя"""
    users = database_read_users_order()
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
    warehouses = database_read_warehouses()
    for warehouse in warehouses:
        if warehouse_id == warehouse['warehouse_id']:
            address = warehouse['warehouse_address']
            return address


def get_warehouses_address() -> list:
    """Функция для получения списка адресов складов"""
    warehouses = database_read_warehouses()
    warehouses_address = [
        dict({
                'warehouse_id': warehouse['warehouse_id'],
                'warehouse_address': warehouse['warehouse_address']
            }) for warehouse in warehouses
    ]
    return warehouses_address


def get_warehouses_boxes(params_by_user: dict) -> list:
    """Функция для получения списка всех доступных боксов с указаннными пользователем параметрами на складе"""
    boxes = []
    warehouses = database_read_warehouses()
    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses
                       if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if (box['box_size'] == params_by_user['box_size'] and
                    box['box_type'] == params_by_user['box_type'] and
                    not box['box_reserved']):
                boxes.append(box)
    return boxes


def get_box_floor(params_by_user: dict) -> list:
    """Функция для получения этажа на котором находится выбранный бокс"""
    warehouses = database_read_warehouses()
    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if box['box_id'] == params_by_user['box_id']:
                return box['box_floor']


def get_box_price(params_by_user: dict) -> list:
    """Функция для получения стоимости выбранного бокса"""
    warehouses = database_read_warehouses()
    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if box['box_id'] == params_by_user['box_id']:
                return box['box_price']

                
def create_unique_qr(users: list) -> str:
    users_orders = [user['orders'] for user in users]
    all_qr_codes = []
    for user_orders in users_orders:
        for order in user_orders:
            all_qr_codes.append(int(order['qr_code']))

    random_qr = random.randint(10000, 99999)
    while random_qr in all_qr_codes:
        random_qr = random.randint(10000, 99999)

    return str(random_qr)


def add_new_user_order(user_id: int, order_params: dict):
    """Функция добавления нового заказа в базу"""
    users = database_read_users_order()

    for user in users:
        if user['user_id'] == user_id:
            new_order = {
                "order_id": random.randint(1, 200),
                "qr_code": create_unique_qr(users),
                "warehouse_id": order_params['warehouse_id'],
                "box_id": order_params['box_id'],
                "start_date": order_params['start_date'],
                "end_date": order_params['end_date'],
            }
            user['orders'].append(new_order)

    database_write_users_order(users)
    reserve_box_in_warehouse(order_params)


def reserve_box_in_warehouse(order_params: dict):
    """Функция помечает оплаченный пользователем бокс как зарезервированный"""
    warehouses = database_read_warehouses()
    for warehouse in warehouses:
        if warehouse['warehouse_id'] == order_params['warehouse_id']:
            for box in warehouse['boxes']:
                if box['box_id'] == order_params['box_id']:
                    box.update({'box_reserved': True})
    database_write_warehouses(warehouses)


def get_warehouses_location(user_pos: tuple) -> list:
    """Функция для получения ближайшего склада до пользователя на основе его местоположения"""
    warehouses = database_read_warehouses()
    nearest_warehouses = []
    for warehouse in warehouses:
        new_location = dict()
        new_location["warehouse_id"] = warehouse['warehouse_id']
        new_location["warehouse_address"] =  warehouse['warehouse_address']
        new_location["distance"] = distance.distance(
            (user_pos[0], user_pos[1]),
            (warehouse['coordiantes']['latitude'], warehouse['coordiantes']['longitude'])
        ).km
        nearest_warehouses.append(new_location)
    nearest_warehouses = sorted(nearest_warehouses, key=lambda k: k['distance'])
    return nearest_warehouses[0]