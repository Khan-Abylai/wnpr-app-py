import base64
import logging
import ctypes as c
import datetime
import os
import time
from collections import Counter
from ctypes import *

import cv2
import numpy as np
import requests
from PIL import Image

import src.constants as constants
import src.utils as utils

logging.basicConfig(filename='/home/parqour/wnpr_logs/wnprapp.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')
class Application(object):

    def __init__(self, camera_ip, template_matching, server):

        os.environ[
            'PATH'] = constants.lib_path + os.pathsep + os.environ['PATH']

        # For camera
        #self.video_path = 'rtsp://admin:campas123.@{}/media/video1'.format(camera_ip)

        # For video
        self.video_path = constants.video_path

        self.DTKWNR = cdll.LoadLibrary(constants.DTKWNRLib)
        self.DTKVID = cdll.LoadLibrary(constants.DTKVIDLib)

        self.camera_ip = camera_ip
        self.template_matching = template_matching
        self.server = server

        self.debug_mode = constants.debug_mode

        self.wn_texts = {self.camera_ip: []}
        self.packages = {self.camera_ip: {}}

        self.first_wn_number = {}
        self.second_wn_number = {}

        self.last_event = datetime.datetime.now()

    def FrameCapturedCallback(self, hVideoCapture: int, hFrame: int,
                              customObject: int):

        # print "Frame received"
        hEngine = customObject
        self.DTKWNR.WNREngine_PutFrame(c_void_p(hEngine), c_void_p(hFrame),
                                       c_uint64(0))

    def CaptureErrorCallback(self, hVideoCapture, errorCode, customObject):

        if errorCode != 3:
            print("Capture error: %d", errorCode)
        global stopFlag
        stopFlag = True

    def send_pkgs(self, ip: str):
        if utils.check_wn_count_direction(self.first_wn_number,
                                          self.second_wn_number):

            counter_list = Counter(self.wn_texts[ip])
            common_wn_number = counter_list.most_common(1)[0][0]
            self.wn_texts[ip] = [item for item in self.wn_texts[ip] if item != common_wn_number]

            frame_img = self.packages[ip]['frame']
            wn_img = self.packages[ip]['wn_img']
            wn_rect = self.packages[ip]['wn_rect']
            retval, frame_img_buffer = cv2.imencode('.jpg', frame_img)
            frame_img_b64 = base64.b64encode(frame_img_buffer).decode('utf-8')
            retval, wn_img_buffer = cv2.imencode('.jpg', wn_img)
            wn_img_b64 = base64.b64encode(wn_img_buffer).decode('utf-8')
            direction_to = utils.sending_direction(common_wn_number,
                                                   self.first_wn_number,
                                                   self.second_wn_number)

            data = {
                'ip_address': ip,
                'event_time': str(datetime.datetime.now()).split('.')[0],
                'car_number': common_wn_number,
                'car_picture': frame_img_b64,
                'wn_picture': wn_img_b64,
                'wn_rect': wn_rect,
                'direction': direction_to
            }
            print("sent",
                  str(datetime.datetime.now()).split('.')[0],
                  ip, common_wn_number,
                  direction_to)
            try:
                r = requests.post("http://" + self.server + ":8000/handle",
                                  data=data)
                print("sent",
                      str(datetime.datetime.now()).split('.')[0],
                      r.status_code, r.text, ip, common_wn_number,
                      direction_to)

                self.wn_texts[ip] = list(
                    filter(lambda number: number != common_wn_number,
                           self.wn_texts[ip]))

                self.last_event = datetime.datetime.now()

            except Exception as e:
                pass
                #print(ip, 'Error in post request:', e)
        else:
            data = {"ip_address": ip}
            #print("----------------------------")
            try:
                r = requests.post("http://" + self.server +
                                  ":8000/not_resolved",
                                  data=data)
                print("loop: sent ************************", r.status_code,
                      r.text, ip)
            except Exception as e:
                pass
                #print(ip, 'Error in post request:', e)

    def WagonNumberDetectedCallback(self, hVideoCapture: int, hWagonNum: int):

        # get wagon number text
        wagonNumberText = c.create_string_buffer(100)
        self.DTKWNR.WagonNumber_GetText(c_void_p(hWagonNum), wagonNumberText,
                                        c_int(100))

        # get confidence
        conf = self.DTKWNR.WagonNumber_GetConfidence(c_void_p(hWagonNum))

        # get wagon number coordinates
        x = self.DTKWNR.WagonNumber_GetX(c_void_p(hWagonNum))
        y = self.DTKWNR.WagonNumber_GetY(c_void_p(hWagonNum))
        w = self.DTKWNR.WagonNumber_GetWidth(c_void_p(hWagonNum))
        h = self.DTKWNR.WagonNumber_GetHeight(c_void_p(hWagonNum))

        centers = utils.calculat_wn_center(x, y, w, h)

        wagon_label = str(wagonNumberText.value.decode())

        if int(
                conf
        ) >= constants.rec_threshold and self.template_matching.has_matching_template(
                wagon_label):

            # get recognition zone number (0 - if zones not defined)
            zone = self.DTKWNR.WagonNumber_GetZone(c_void_p(hWagonNum))

            # get information of symbols
            num_symbols = self.DTKWNR.WagonNumber_GetSymbolsCount(
                c_void_p(hWagonNum))
            for i in range(0, num_symbols - 1):
                symb = self.DTKWNR.WagonNumber_GetSymbol(
                    c_void_p(hWagonNum), i)
                symb_c = self.DTKWNR.WagonNumber_GetSymbolConfidence(
                    c_void_p(hWagonNum), i)
                symb_x = self.DTKWNR.WagonNumber_GetSymbolX(
                    c_void_p(hWagonNum), i)
                symb_y = self.DTKWNR.WagonNumber_GetSymbolY(
                    c_void_p(hWagonNum), i)
                symb_w = self.DTKWNR.WagonNumber_GetSymbolWidth(
                    c_void_p(hWagonNum), i)
                symb_h = self.DTKWNR.WagonNumber_GetSymbolHeight(
                    c_void_p(hWagonNum), i)

            img_width = c_int(0)
            img_height = c_int(0)
            img_stride = c_int(0)

            # get frame image
            buf = POINTER(c_ubyte)()
            self.DTKWNR.WagonNumber_GetImageBuffer(c_void_p(hWagonNum),
                                                   byref(buf),
                                                   byref(img_width),
                                                   byref(img_height),
                                                   byref(img_stride))
            data = np.ctypeslib.as_array(buf,
                                         shape=(img_width.value *
                                                img_height.value * 3, ))
            frame = Image.frombuffer('RGB',
                                     (img_width.value, img_height.value), data,
                                     "raw", "RGB")

            frame = utils.convert_img(frame)

            self.DTKWNR.WagonNumber_FreeImageBuffer(buf)

            # get wagon number image
            buf = POINTER(c_ubyte)()
            self.DTKWNR.WagonNumber_GetWagonNumberImageBuffer(
                c_void_p(hWagonNum), byref(buf), byref(img_width),
                byref(img_height), byref(img_stride))
            data = np.ctypeslib.as_array(buf,
                                         shape=(img_width.value *
                                                img_height.value * 3, ))
            wn_img = Image.frombuffer('RGB',
                                      (img_width.value, img_height.value),
                                      data, "raw", "RGB")

            wn_img = utils.convert_img(wn_img)

            self.DTKWNR.WagonNumber_FreeImageBuffer(buf)

            if self.debug_mode:
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, wagonNumberText.value.decode(), (20, 60),
                            font, 2, (0, 0, 255), 3, cv2.LINE_AA)
                cv2.imshow(self.camera_ip + "_res", frame)
                cv2.imshow(self.camera_ip + "_wn", wn_img)
                k = cv2.waitKey(1)
                if k == 27:
                    exit()

            if utils.old_data(self.last_event):
                self.wn_texts[self.camera_ip] = []
                self.first_wn_number = {}
                self.second_wn_number = {}

            self.wn_texts[self.camera_ip].append(wagon_label)
            self.packages[self.camera_ip]['frame'] = frame
            self.packages[self.camera_ip]['wn_img'] = wn_img
            self.packages[self.camera_ip]['wn_rect'] = [x, y, w, h]

            utils.collect_wn_coordinates(centers, wagon_label,
                                         self.first_wn_number,
                                         self.second_wn_number)

            if utils.check_count_wn(self.wn_texts[self.camera_ip]):
                self.send_pkgs(self.camera_ip)

    def run(self):

        stopFlag = False

        # define callback functions
        FrameCapturedCallback_type = CFUNCTYPE(None, c_void_p, c_void_p,
                                               c_uint64)
        CaptureErrorCallback_type = CFUNCTYPE(None, c_void_p, c_int, c_void_p)
        WagonNumberDetectedCallback_type = CFUNCTYPE(None, c_void_p, c_void_p)

        callback_FrameCaptured = FrameCapturedCallback_type(
            self.FrameCapturedCallback)
        callback_CaptureError = CaptureErrorCallback_type(
            self.CaptureErrorCallback)
        callback_WagonNumberDetected = WagonNumberDetectedCallback_type(
            self.WagonNumberDetectedCallback)

        # define functions return type
        self.DTKWNR.WNRParams_Create.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNREngine_Create.restype = c.POINTER(c.c_void_p)
        self.DTKVID.VideoCapture_Create.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNREngine_ReadFromFile.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNREngine_ReadFromMemFile.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNREngine_ReadFromURL.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNREngine_ReadFromImageBuffer.restype = c.POINTER(
            c.c_void_p)
        self.DTKWNR.WNRResult_GetWagonNumber.restype = c.POINTER(c.c_void_p)
        self.DTKWNR.WNRParams_AddZonePointF.argtypes = [
            c.POINTER(c.c_void_p), c.c_int, c.c_float, c.c_float
        ]

        # create WNRParams object and define all settings
        hParams = self.DTKWNR.WNRParams_Create()
        self.DTKWNR.WNRParams_set_MinWidth(hParams, 80)
        self.DTKWNR.WNRParams_set_MaxWidth(hParams, 300)
        self.DTKWNR.WNRParams_set_RotateAngle(hParams, 0)
        self.DTKWNR.WNRParams_set_BurnFormatString(
            hParams, "%DATETIME% | Wagon number: %NUMBER%")
        self.DTKWNR.WNRParams_set_BurnPosition(hParams, 1)  # Right-Top corner

        # Add rectangular zone to process whole image
        # to define zones using fixed coordinates (in pixels) use functions without F postfix.
        zone_idx = self.DTKWNR.WNRParams_AddZone(hParams)
        self.DTKWNR.WNRParams_AddZonePointF(hParams, zone_idx, 0.0, 0.0)
        self.DTKWNR.WNRParams_AddZonePointF(hParams, zone_idx, 1.0, 0.0)
        self.DTKWNR.WNRParams_AddZonePointF(hParams, zone_idx, 1.0, 1.0)
        self.DTKWNR.WNRParams_AddZonePointF(hParams, zone_idx, 0.0, 1.0)

        # remove all zones
        while self.DTKWNR.WNRParams_GetZonePointsCount(hParams) > 0:
            self.DTKWNR.WNRParams_RemoveZone(hParams, 0)

        # create WNREngine object for processing images
        hEngine = self.DTKWNR.WNREngine_Create(hParams, True,
                                               callback_WagonNumberDetected)

        ret = self.DTKWNR.WNREngine_IsLicensed(hEngine)

        # check license
        utils.check_license(ret)

        hCpature = self.DTKVID.VideoCapture_Create(callback_FrameCaptured,
                                                   callback_CaptureError,
                                                   hEngine)

        video_encode = self.video_path.encode('utf-8')

        self.DTKVID.VideoCapture_StartCaptureFromFile(hCpature, video_encode)

        print("Video started")

        while not stopFlag:
            time.sleep(1)

        # stop capture
        self.DTKVID.VideoCapture_StopCapture(hCpature)

        # destroy objects
        self.DTKVID.VideoCapture_Destroy(hCpature)
        self.DTKWNR.WNREngine_Destroy(hEngine)
