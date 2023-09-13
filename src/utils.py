import datetime
from collections import Counter

import cv2
import numpy as np
from PIL.Image import Image

import src.constants as constants


def check_count_wn(wn_texts: list) -> bool:
    # Iterate over the counter items
    counter_list = Counter(wn_texts)
    for wn_number, count in counter_list.items():
        if count >= constants.wn_count:
            return True
    else:
        return False


def calculat_wn_center(x: int, y: int, w: int, h: int) -> int:
    center_x = x + w / 2
    center_y = y + h / 2
    return center_x, center_y


def convert_img(frame: Image) -> np.ndarray:
    frame = np.array(frame)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame


def check_license(ret: int):
    if ret != 0:
        if ret == 1:
            print("No License")
        if ret == 2:
            print("No channles available")
        if ret == 3:
            print("Cannot validate trial license")
        exit()


def determine_direction(number_data: dict):  # Определяет направление
    """
    Определяет направление.
    """
    num = number_data['coordinates'][0][0] - number_data['coordinates'][-1][0]
    if abs(num) > constants.direction_threshold:
        if num > 0:
            number_data['direction'] = 'forward'  # <-
        elif num < 0:
            number_data['direction'] = 'reverse'  # ->


def check_wn_count_direction(wn_data: dict) -> bool:  # проверка к отправке
    """
    Проверяет направление и сбрасывает счетчик.
    """
    for wn_number in wn_data:
        number_data = wn_data[wn_number]

        if number_data['wn_count'] >= constants.wn_count:
            determine_direction(number_data)
            number_coordinate = number_data['coordinates'][-1]
            number_data.update({
                    'coordinates': [number_coordinate, number_coordinate],
                    'wn_count': 1
                })
            return True
    return False


def sending_direction(wn_number: str, wn_data: dict) -> str:  # отправка направление
    """
    Отправляет направление и очищает старые данные.
    """
    direction = wn_data[wn_number]['direction']
    index_limit = len(wn_data) - constants.wn_count - 1

    for index, keys_wn_number in enumerate(wn_data.copy()):
        if keys_wn_number == wn_number: break
        if index_limit >= index:
            wn_data.pop(keys_wn_number)

    return direction


def collect_wn_coordinates(coordinate: tuple, wn_number: str,
                           wn_data: dict) -> bool:
    """
    Собирает координаты и обновляет счетчик.
    """
    if wn_number not in wn_data:
        wn_data[wn_number] = {
            'coordinates': [coordinate, coordinate], # [first, last]
            'wn_count': 1, 'direction': None
        }
        return True

    last_coordinate = wn_data[wn_number]['coordinates'][-1]
    difference_y = abs(last_coordinate[1] - coordinate[1])
    difference_x = abs(last_coordinate[0] - coordinate[0])

    if (difference_y < constants.select_wn_threshold and
            difference_x < constants.select_wn_threshold):
        wn_data[wn_number]['wn_count'] += 1
        wn_data[wn_number]['coordinates'][-1] = coordinate
    return False


def old_data(last_event: datetime.datetime) -> bool:
    current_time = datetime.datetime.now()
    time_difference = current_time - last_event
    if (time_difference.seconds // 60) % 60 >= constants.old_data_threshold:
        return True
    return False
