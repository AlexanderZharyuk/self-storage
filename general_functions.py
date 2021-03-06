import configparser
import os
import random
import json

from string import digits
from geopy import distance

from validate_exceptions import *

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')


def create_database() -> None:
    """Создание файла базы данных"""
    db_folder = os.path.split(CONFIG['DEFAULT']['DATABASE_PATH'])[0]
    os.makedirs(db_folder, exist_ok=True)

    with open(CONFIG['DEFAULT']['DATABASE_PATH'], 'w', encoding='"utf-8"') as file:
        empty_base = []
        json.dump(empty_base, file)


def load_warehouses() -> list:
    """Загрузка данных о складах"""
    warehouses_info_folder = os.path.split(CONFIG['DEFAULT']['DATABASE_PATH'])[0]
    os.makedirs(warehouses_info_folder, exist_ok=True)

    with open(CONFIG['DEFAULT']['WAREHOUSES_INFO_PATH'], 'r', encoding='utf-8') as json_file:
        warehouses = json.load(json_file)

    return warehouses


def load_users() -> list:
    """Загрузка данных об юзерах"""
    with open(CONFIG['DEFAULT']['DATABASE_PATH'], 'r', encoding="utf-8") as file:
        users = json.load(file)

    return users


def is_new_user(user_id: int) -> bool:
    """Функция возвращает True или False в зависимости от того - есть ли пользователь в базе данных"""
    users = load_users()
    users_ids = [user['user_id'] for user in users if user['user_id'] == user_id]
    return not bool(users_ids)


def get_orders(user_id: int) -> list:
    """Функция для получения списка заказов пользователя"""
    users = load_users()
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


def get_warehouse_address(warehouse_id) -> str:
    """Функция для получения адреса по номеру склада"""
    warehouses = load_warehouses()
    for warehouse in warehouses:
        if warehouse_id == warehouse['warehouse_id']:
            address = warehouse['warehouse_address']
            return address


def get_warehouses_address() -> list:
    """Функция для получения списка адресов складов"""
    warehouses = load_warehouses()
    warehouses_address = [
        dict({'warehouse_id': warehouse['warehouse_id'],
              'warehouse_address': warehouse['warehouse_address']}) for warehouse in warehouses]
    return warehouses_address


def get_warehouses_boxes(params_by_user: dict) -> list:
    """Функция для получения списка всех доступных боксов с указаннными пользователем параметрами на складе"""
    warehouses = load_warehouses()
    boxes = []

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
    warehouses = load_warehouses()
    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses if
                       warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if box['box_id'] == params_by_user['box_id']:
                return box['box_floor']


def get_box_price(params_by_user: dict) -> list:
    """Функция для получения стоимости выбранного бокса"""
    warehouses = load_warehouses()
    warehouse_boxes = [warehouse['boxes'] for warehouse in warehouses
                       if warehouse['warehouse_id'] == params_by_user['warehouse_id']]
    for boxes_list in warehouse_boxes:
        for box in boxes_list:
            if box['box_id'] == params_by_user['box_id']:
                return box['box_price']

                
def create_unique_qr() -> str:
    with open(CONFIG['DEFAULT']['DATABASE_PATH'], 'r') as file:
        all_users = json.load(file)

    all_orders = [order['orders'] for order in all_users]
    all_qr_codes = []
    for user_order in all_orders:
        for qr_code in user_order:
            all_qr_codes.append(int(qr_code['qr_code']))

    random_qr_numbers = random.randint(10000, 99999)
    while random_qr_numbers in all_qr_codes:
        random_qr_numbers = random.randint(10000, 99999)

    return str(random_qr_numbers)


def add_new_user_order(user_id: int, order_params: dict):
    """Функция добавления нового заказа в базу"""
    users = load_users()
    for user in users:
        if user['user_id'] == user_id:
            new_order = {
                "order_id": random.randint(1, 200),
                "qr_code": create_unique_qr(),
                "warehouse_id": order_params['warehouse_id'],
                "box_id": order_params['box_id'],
                "start_date": order_params['start_date'],
                "end_date": order_params['end_date'],
            }
            user['orders'].append(new_order)

    with open(CONFIG['DEFAULT']['DATABASE_PATH'], 'w', encoding="utf-8") as json_file:
        json.dump(users, json_file, indent=4, ensure_ascii=False)

    reserve_box_in_warehouse(order_params)


def reserve_box_in_warehouse(order_params: dict):
    """Функция помечает оплаченный пользователем бокс как зарезервированный"""
    warehouses = load_warehouses()
    for warehouse in warehouses:
        if warehouse['warehouse_id'] == order_params['warehouse_id']:
            for box in warehouse['boxes']:
                if box['box_id'] == order_params['box_id']:
                    box.update({'box_reserved': True})

    with open(CONFIG['DEFAULT']['WAREHOUSES_INFO_PATH'], 'w', encoding="utf-8") as json_file:
        json.dump(warehouses, json_file, indent=4, ensure_ascii=False)


def get_warehouses_location(user_pos: tuple) -> dict:
    """Функция для получения ближайшего склада до пользователя на основе его местоположения"""
    warehouses = load_warehouses()
    nearest_warehouses = []
    for warehouse in warehouses:
        new_location = dict()
        new_location["warehouse_id"] = warehouse['warehouse_id']
        new_location["warehouse_address"] = warehouse['warehouse_address']
        new_location["distance"] = distance.distance(
            (user_pos[0], user_pos[1]),
            (warehouse['coordiantes']['latitude'], warehouse['coordiantes']['longitude'])
        ).km
        nearest_warehouses.append(new_location)
    nearest_warehouses = sorted(nearest_warehouses, key=lambda k: k['distance'])
    return nearest_warehouses[0]
