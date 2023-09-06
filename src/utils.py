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
    # Convert Pillow Image to NumPy array
    frame = np.array(frame)

    # Convert RGB image to BGR
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


def determine_direction(wn_number: dict):
    num = wn_number['coordinates'][0][0] - wn_number['coordinates'][-1][0]
    if abs(num) > constants.difference_coordinate:
        if num > 0:
            wn_number['direction'] = 'forward'  # <-
        elif num < 0:
            wn_number['direction'] = 'reverse'  # ->
    wn_number['coordinates'] = []


def check_wn_count_direction(
        first_wn_number: dict,
        second_wn_number: dict) -> bool:  # проверка к отправке
    for wn_number in first_wn_number:
        if len(first_wn_number[wn_number]
               ['coordinates']) >= constants.wn_count or len(
                   second_wn_number[wn_number]
                   ['coordinates']) >= constants.wn_count:
            first_wn_number = first_wn_number[wn_number]
            second_wn_number = second_wn_number[wn_number]

            if len(first_wn_number['coordinates']) >= constants.wn_count:
                determine_direction(first_wn_number)

            elif len(second_wn_number['coordinates']) >= constants.wn_count:
                first_wn_number['coordinates'] = []
                first_wn_number['coordinates'] = second_wn_number[
                    'coordinates'].copy()
                determine_direction(first_wn_number)
                second_wn_number['coordinates'] = []

            return True


def sending_direction(wn_number: str, first_wn_number: dict,
                      second_wn_number: dict) -> str:  # отправка направление
    direction = first_wn_number[wn_number]['direction']
    for index, keys_wn_number in enumerate(first_wn_number.copy()):
        if keys_wn_number == wn_number: break
        if len(first_wn_number) - constants.wn_count - 1 == index:
            first_wn_number.pop(keys_wn_number)
            second_wn_number.pop(keys_wn_number)

    return direction


def collect_wn_coordinates(coordinate: tuple, wn_number: str,
                           first_wn_number: dict,
                           second_wn_number: dict) -> bool:
    if first_wn_number.get(wn_number, True) == True:
        first_wn_number[wn_number] = {
            'coordinates': [coordinate],
            'direction': None,
            'past_coordinate': coordinate
        }
        second_wn_number[wn_number] = {'coordinates': []}
        return True
    else:
        if abs(first_wn_number[wn_number]['past_coordinate'][1] -
               coordinate[1]) < constants.wns_coordinates_threshold:
            first_wn_number[wn_number]['coordinates'] += [coordinate]
            first_wn_number[wn_number]['past_coordinate'] = coordinate
        else:
            second_wn_number[wn_number]['coordinates'] += [coordinate]
        return False


def old_data(last_event: datetime.datetime) -> bool:
    current_time = datetime.datetime.now()
    time_difference = current_time - last_event
    if (time_difference.seconds // 60) % 60 >= constants.old_data_threshold:
        return True
    return False
