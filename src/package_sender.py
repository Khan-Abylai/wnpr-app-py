import requests
from queue import Queue
import datetime
from src.logger_config import logger

class PackageSender:
    SEND_REQUEST_TIMEOUT = 10

    def __init__(self, server_ip):
        self.SERVER_URL = f"http://{server_ip}:8888/rest/cars/event"
        self.shutdown_flag = False
        self.package_queue = Queue()

    def send_request_async(self, data):
        headers = {'Content-Type': 'application/json'}
        return requests.post(self.SERVER_URL, json=data, headers=headers, timeout=self.SEND_REQUEST_TIMEOUT)

    def run(self):
        while not self.shutdown_flag:
            package = self.package_queue.get()
            if package is None:
                continue
            response = self.send_request_async(package)
            logger.info("sent %s %s %s %s %s", response.status_code, response.text, package['ip_address'], package['car_number'], package['direction'])


    def shutdown(self):
        logger.info("Service is shutting down")
        self.shutdown_flag = True
        self.package_queue.put(None)

    def add_package(self, ip, common_wn_number, frame_img_b64, wn_img_b64, wn_rect, direction_to):
        data = {
            'ip_address': ip,
            'event_time': str(datetime.datetime.now()).split('.')[0],
            'car_number': common_wn_number,
            'car_picture': frame_img_b64,
            'lp_picture': wn_img_b64,
            'lp_rect': wn_rect,
            'direction': direction_to
        }
        self.package_queue.put(data)
