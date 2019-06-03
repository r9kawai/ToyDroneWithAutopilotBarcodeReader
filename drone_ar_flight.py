# This source code is recognition are positions from camera image,
# self position, markers position, and read barcode.
# (These are indicate a distance of cm, and a degree of view direction, and a diffrential cm,
# of cource, Those estimates is not accurate! but, Aircraft is repeatedly estimate,
# and move, amend, so Usually works well.)
# Swich a action mode from some modes and submodes, depend on detect marker information.
# If aircraft position is close a marker, It try read a barcode.
# Successfuly, ring a beep sound, then turn 90degree x 2, Alternate to next marker.
# Repeate above.(If it goes well)
# These algorithms have margin for improvement.

import os
import time
import datetime
import math
import numpy as np
import cv2
from drone_ar_assignment import Drone_AR_assignment
from PIL import Image, ImageFont, ImageDraw
from pyzbar.pyzbar import decode
from beep import Beep

MODE_SEARCH_UD = 'SEARCH UP DOWN'
MODE_TO_DIR = 'TO DIRECTION'
MODE_TO_FRONT = 'TO FRONT'
MODE_TO_ALTERNATE = 'TO ALTERNATE'
MODE_MANUAL = 'MANUAL'

SUB_MODE_UP = 'UP'
SUB_MODE_DOWN = 'DOWN'
SUB_MODE_BACK = 'BACK'
SUB_MODE_ALT = 'ALT'

ALTITUDE_MAX = 160
ALTITUDE_MIN = 50
MOVE_MIN = 20
MOVE_MIN_F = 30
MOVE_MIN_B = 20
MOVE_MAX = 80
BARREAD_DISTANCE = 60
MIN_DEGREE = 3

FRAME_W = 960
FRAME_H = 720

DETECT_CYCLE_TIME_MS = 200

PARAM_A_1 = (float)(185)
PARAM_A_2 = (float)(5.1)
PARAM_A_3 = (int)(135)

PARAM_1 = PARAM_A_1
PARAM_2 = PARAM_A_2
PARAM_3 = PARAM_A_3

DETECT_CYCLE_TIME_MS = 200

TTFFONT = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
TTFFONTBOLD = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'
COLOR_BLACK = (0,0,0)
COLOR_RED = (255,0,0)
COLOR_GREEN = (0,255,0)
COLOR_YELLOW = (255,255,0)
COLOR_WHITE = (255,255,255)

class Drone_AR_Flight:
    def __init__(self):
        self.ar_as = Drone_AR_assignment()
    
        self.mode = MODE_SEARCH_UD
        self.sub_mode = SUB_MODE_UP
        self.now_height_cm = int(0)
        self.next_cmd = None
        self.next_cmd_val = 0

        self.frame_no = 0
        self.fps = 0
        self.fps_period = 10
        self.frame_p_m = int(round(time.time() * 1000))
        self.frame = None
        self.gray_frame = None
        self.detects = 0
        self.detect_t = 0

        self.ar_dict_name = cv2.aruco.DICT_6X6_250
        self.ar_dict = cv2.aruco.getPredefinedDictionary(self.ar_dict_name)

        self._marker_reset()

        self.code_latest = ''
        self.code_latest_rect = (0,0,0,0)
        self.code_latest_view = 0

        self.beep = Beep()

        self.font = ImageFont.truetype(TTFFONT,32)
        self.fontbold = ImageFont.truetype(TTFFONTBOLD,32)

    def renew_frame(self, frame, frame_no, now_height, ar_cmd, ar_val):
        self.now_height_cm = now_height
        if hasattr(frame, 'shape'):
            if len(frame.shape) >= 2:
                if frame.shape[1] == FRAME_W:
                    if (frame_no % self.fps_period) == 0:
                        frame_p_m_t = int(round(time.time() * 1000))
                        diff_t = frame_p_m_t - self.frame_p_m
                        self.fps = round(1000*self.fps_period / diff_t)
                        self.frame_p_m = frame_p_m_t

                    self.frame = frame
                    
                    now_t = int(round(time.time() * 1000))
                    dt = now_t - self.detect_t
                    if dt >= DETECT_CYCLE_TIME_MS:
                        self.gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                        self._detect()
                        self._detect2()
                        self.detect_t = int(round(time.time() * 1000))

            self._draw(ar_cmd, ar_val)
            self.frame_no = frame_no
            return

    def _draw(self, ar_cmd, ar_val):
        if self.code_latest_view > 0:
            self.code_latest_view -=1
            cv2.rectangle(self.frame, self.code_latest_rect, (0,196,0), 1)
            puttxt4 = self.code_latest
            cv2.putText(self.frame, puttxt4, (self.code_latest_rect[0],self.code_latest_rect[1]+self.code_latest_rect[3]/2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)

        for i in range(4):
            if self.marker_id[i] == True:
                points = self.marker_pointss[i]
                if self.marker_enable[i] == True:
                    self.alt_ar_to_img(self.frame, points, i)
                    cv2.polylines(self.frame, [points], True, (255,255,0), 2)
                else:
                    cv2.polylines(self.frame, [points], True, (0,255,0), 1)
        return

    def draw_txt(self, fromarray, ar_cmd, ar_val):
        drawtxt = ImageDraw.Draw(fromarray)
        puttxt = ('%3d' % self.fps) + '.fps  ' + str(self.detects) + '.detects'
        self.draw_bold_text(drawtxt, puttxt, 10, 10, COLOR_BLACK, COLOR_GREEN)

        if ar_cmd == MODE_MANUAL:
            puttxt = ar_cmd
            color = COLOR_BLACK
        else:
            puttxt = 'AUTO : ' + self.mode + ' ' + self.sub_mode + ' ' + ar_cmd + ' ' + str(ar_val)
            color = COLOR_RED
        self.draw_bold_text(drawtxt, puttxt, 10, 560, color, COLOR_WHITE)

        puttxt = 'dist     '
        puttxt += ('%3d' % self.marker_distances[0]) + '       '
        puttxt += ('%3d' % self.marker_distances[1]) + '       '
        puttxt += ('%3d' % self.marker_distances[2]) + '       '
        puttxt += ('%3d' % self.marker_distances[3]) + ' cm'
        self.draw_bold_text(drawtxt, puttxt, 10, 590, COLOR_BLACK, COLOR_GREEN)

        puttxt = ' gap '
        puttxt += ('%3d' % self.marker_diff_cm[0][0]) + ',' + ('%3d' % self.marker_diff_cm[0][1]) + '   '
        puttxt += ('%3d' % self.marker_diff_cm[1][0]) + ',' + ('%3d' % self.marker_diff_cm[1][1]) + '   '
        puttxt += ('%3d' % self.marker_diff_cm[2][0]) + ',' + ('%3d' % self.marker_diff_cm[2][1]) + '   '
        puttxt += ('%3d' % self.marker_diff_cm[3][0]) + ',' + ('%3d' % self.marker_diff_cm[3][1]) + ' cm'
        self.draw_bold_text(drawtxt, puttxt, 10, 620, COLOR_BLACK, COLOR_GREEN)

        puttxt = ' dir     '
        puttxt += ('%3d' % self.marker_degree[0]) + '       '
        puttxt += ('%3d' % self.marker_degree[1]) + '       '
        puttxt += ('%3d' % self.marker_degree[2]) + '       '
        puttxt += ('%3d' % self.marker_degree[3]) + ' degree'
        self.draw_bold_text(drawtxt, puttxt, 10, 650, COLOR_BLACK, COLOR_GREEN)

        puttxt = 'Z-tilt   '
        puttxt += ('%3d' % self.marker_ztilt[0]) + '       '
        puttxt += ('%3d' % self.marker_ztilt[1]) + '       '
        puttxt += ('%3d' % self.marker_ztilt[2]) + '       '
        puttxt += ('%3d' % self.marker_ztilt[3]) + ' degree'
        self.draw_bold_text(drawtxt, puttxt, 10, 680, COLOR_BLACK, COLOR_GREEN)
        return

    def _detect(self):
        corners, ids, rejects = cv2.aruco.detectMarkers(self.gray_frame, self.ar_dict)
        self.detects = len(corners)
        if self.detects == 0:
            for i in range(4):
                dt = int(round(time.time() * 1000)) - self.marker_time[i]
                if dt > 1000:
                    self.marker_enable[i] = False
                else:
                    self.marker_enable[i] = True
            return

        detect = [False, False, False, False]
        for i, corner in enumerate(corners):
            points = corner[0].astype(np.int32)
            p0 = points[0]
            p1 = points[1]
            p2 = points[2]
            p3 = points[3]
            id = int(ids[i][0])
            if id < 4 and len(points) == 4:
                # enable marker flag
                detect[id] = True
                self.marker_id[id] = True
                
                # take a marker corner points
                self.marker_pointss[id] = points

                # take a distance of to marker (method of apparent size)
                # (apparent size is sum of outer 4line length) 
                normsum = float(cv2.norm(p0,p1) + cv2.norm(p1,p2) + cv2.norm(p2,p3) + cv2.norm(p3, p0))
                dist = (float)(100) / (normsum / PARAM_1)
                self.marker_distances[id] = (int)(dist)

                # take a center of marker corner points
                cx = int(0)
                cy = int(0)
                for ii in range(4):
                    cx += self.marker_pointss[id][ii][0]
                    cy += self.marker_pointss[id][ii][1]
                cx /= 4
                cy /= 4

                # take a difference from screen center to the center of marker
                dcx = cx - (FRAME_W/2)
                dcy = cy - (FRAME_H/2)

                # take a cm/dot as in the marker
                cmpdot = (PARAM_2*4) / normsum

                # take a difference [cm] to the marker as space
                dcm_x_f = cmpdot * (float)(dcx)
                dcm_x = int(round(cmpdot*dcx))
                dcm_y = int(round(cmpdot*dcy))
                dcm_y += int(round(cmpdot*PARAM_3))
                self.marker_diff_cm[id][0] = dcm_x
                self.marker_diff_cm[id][1] = dcm_y

                # take a direction degree to the marker
                # (as tangent with distance and diffrence)
                if dist != 0 and dcm_x != 0:
                    deg = 0
                    if dcm_x > 0:
                        deg = int(round(math.degrees( math.tan(dcm_x_f/dist*-1) )))
                        deg *= -1
                    else:
                        dcm_x_f = abs(dcm_x_f)
                        deg = int(round(math.degrees( math.tan(dcm_x_f/dist*-1) )))
                    self.marker_degree[id] = deg

                # take a z-tilt of the marker
                # (as square distortion)
                x0 = self.marker_pointss[id][0][0]
                y0 = self.marker_pointss[id][0][1]
                x1 = self.marker_pointss[id][1][0]
                y1 = self.marker_pointss[id][1][1]
                x2 = self.marker_pointss[id][2][0]
                y2 = self.marker_pointss[id][2][1]
                x3 = self.marker_pointss[id][3][0]
                y3 = self.marker_pointss[id][3][1]
                deg1 = self._get_2point_degree(x0,y0, x1,y1)
                deg2 = self._get_2point_degree(x3,y3, x2,y2)
                deg = deg1 + deg2
                self.marker_ztilt[id] = deg

        # renew record a detect time of the marker
        for i in range(4):
            if detect[i] == True:
                self.marker_time[i] = int(round(time.time() * 1000))

        for i in range(4):
            dt = int(round(time.time() * 1000)) - self.marker_time[i]
            if dt > 1000:
                self.marker_enable[i] = False
            else:
                self.marker_enable[i] = True

        return

    def _detect2(self):
        if self.marker_enable[self.choise_marker] == True:
            if self.marker_distances[self.choise_marker] < BARREAD_DISTANCE:
                if self.code_flag == False:
#                   self._try_read_barcode()
                    self.log_ar_code(self.choise_marker)
        return

    def _try_read_barcode(self):
        decoded = decode(self.gray_frame)
        if len(decoded) > 0:
            rcode = str(decoded[0].type) + ':' + str(decoded[0].data)
            rrect = decoded[0].rect
            self.code_latest = rcode
            self.code_latest_rect = rrect
            self.beep.on()
            self.code_latest_view = 60
            self.code_flag = True
            print('found code:', self.code_latest)

    def get_latest_barcode(self):
        return self.code_latest

    def _marker_sel(self):
        for i in range(4):
            if self.marker_id[i] == True:
                return i
        return 0

    def get_command(self):
        if self.next_cmd != None:
            cmd = self.next_cmd
            val = self.next_cmd_val
            self.next_cmd = None
            self.next_cmd_val = 0
            return cmd, val

        cmd = 'stay'
        val = 0
    
        if self.mode == MODE_SEARCH_UD:
            self.choise_marker = self._marker_sel()
            if self.marker_enable[self.choise_marker] == True:
                self.mode = MODE_TO_DIR
            else:
                if self.now_height_cm > ALTITUDE_MAX:
                    self.sub_mode = SUB_MODE_DOWN
                if self.now_height_cm < ALTITUDE_MIN:
                    self.sub_mode = SUB_MODE_UP

                if self.sub_mode == SUB_MODE_UP:
                    cmd = 'up'
                    val = MOVE_MIN
#                   self.next_cmd = 'rotateRight'
#                   self.next_cmd_val = 30
                elif self.sub_mode == SUB_MODE_DOWN:
                    cmd = 'down'
                    val = MOVE_MIN
#                   self.next_cmd = 'rotateRight'
#                   self.next_cmd_val = 30

        elif self.mode == MODE_TO_DIR:
            deg = self.marker_degree[self.choise_marker]
            if abs(deg) > MIN_DEGREE:
                if deg > 0:
                    cmd = 'rotateRight'
                    val = deg
                else:
                    cmd = 'rotateLeft'
                    val = deg*(-1)
            else:
                self.mode = MODE_TO_FRONT

        elif self.mode == MODE_TO_FRONT:
            dcm_x = self.marker_diff_cm[self.choise_marker][0]
            dcm_y = self.marker_diff_cm[self.choise_marker][1]
            distcm = self.marker_distances[self.choise_marker]
            if self.marker_enable[self.choise_marker] == False:
                cmd = 'back'
                val = MOVE_MIN_B
            elif dcm_x > MOVE_MIN:
                cmd = 'right'
                val = dcm_x
            elif dcm_x < -1*(MOVE_MIN):
                cmd = 'left'
                val = dcm_x*(-1)
            elif dcm_y > MOVE_MIN:
                cmd = 'down'
                val = dcm_y
            elif dcm_y < -1*(MOVE_MIN):
                cmd = 'up'
                val = dcm_y*(-1)
            elif distcm > BARREAD_DISTANCE:
                cmd = 'forward'
                if (distcm - BARREAD_DISTANCE) > MOVE_MAX:
                    val = MOVE_MAX
                else:
                    val = (distcm - BARREAD_DISTANCE)
                if val < MOVE_MIN_F:
                    val = MOVE_MIN_F
                else:
                    self.next_cmd = 'stay'
                    self.next_cmd_val = 0
            elif (distcm < BARREAD_DISTANCE) and (distcm > 0):
                zdeg = self.marker_ztilt[self.choise_marker]
                if abs(zdeg) > MIN_DEGREE:
                    if zdeg > 0:
                        cmd = 'rotateRight'
                        val = zdeg
                    else:
                        cmd = 'rotateLeft'
                        val = zdeg*(-1)
                else:
#                   if abs(abs(dcm_y) - MOVE_MIN) < MOVE_MIN:
#                       if dcm_y > 0:
#                           cmd = 'down'
#                           val = MOVE_MIN
#                       else:
#                           cmd = 'up'
#                           val = MOVE_MIN
                    cmd = 'back'
                    val = MOVE_MIN_B

            else:
                cmd = 'stay'
                val = 0
            if self.code_flag == True:
                self.mode = MODE_TO_ALTERNATE
                self.sub_mode = SUB_MODE_BACK
                cmd = 'back'
                val = BARREAD_DISTANCE
                self.next_cmd = 'rotateLeft'
                self.next_cmd_val = 90

        elif self.mode == MODE_TO_ALTERNATE:
            if self.sub_mode == SUB_MODE_BACK:
                cmd = 'rotateLeft'
                val = 90
                self.sub_mode = SUB_MODE_ALT
            elif self.sub_mode == SUB_MODE_ALT:
                self.mode = MODE_SEARCH_UD
                self.sub_mode = SUB_MODE_UP
                self._marker_reset()
                cmd = 'stay'
                val = 0

        else:
            print('MODE Err')

        return cmd, val

    def draw_bold_text(self, drawtxt, text, x, y, color1, color2):
        drawtxt.text((x+2,y-2), text, color2, font=self.fontbold)
        drawtxt.text((x+2,y+2), text, color2, font=self.fontbold)
        drawtxt.text((x-2,y-2), text, color2, font=self.fontbold)
        drawtxt.text((x-2,y+2), text, color2, font=self.fontbold)
        drawtxt.text((x,y), text, color1, font=self.font)
        return

    def _get_2point_degree(self, ax, ay, ax2, ay2):
        radian = math.atan2(ay2 - ay, ax2 - ax)
        return (int)(round(math.degrees(radian)))

    def _marker_reset(self):
        self.choise_marker = 0
        self.marker_id = [False, False, False, False]
        self.marker_time = [int(0), int(0), int(0), int(0)]
        self.marker_enable = [False, False, False, False]
        self.marker_inframe = [int(0), int(0), int(0), int(0)]
        self.marker_pointss = [[[float(0),float(0)],[float(0),float(0)],[float(0),float(0)],[float(0),float(0)]]]*4
        self.marker_distances = [int(0), int(0), int(0), int(0)]
        self.marker_diff_cm = [ [int(0), int(0)],[int(0), int(0)],[int(0), int(0)],[int(0), int(0)] ]
        self.marker_degree = [int(0), int(0), int(0), int(0)]
        self.marker_ztilt = [int(0), int(0), int(0), int(0)]
        self.code_flag = False
        self.chase_marker = int(-1)
        return

    def alt_ar_to_img(self, frame, points, i):
        iconimg = self.ar_as.ar_to_img(i)
        h, w = iconimg.shape[:2]
        x = points[0][0]
        y = points[0][1]
        frame[0:h, 0:w] = iconimg
        return

    def log_ar_code(self, arcode):
        decoded = self.ar_as.ar_to_name(arcode)
        self.code_latest = decoded
        self.beep.on()
        self.code_latest_view = 60
        self.code_flag = True
        print('found code:', self.code_latest)
        return

#eof

