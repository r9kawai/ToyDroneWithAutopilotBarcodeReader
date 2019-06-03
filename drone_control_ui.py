# This source code is create UI with Tkinter, glue a some components.

import sys
import numpy as np
from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import pytz
import datetime
import cv2
import os
import time
from drone_ar_flight import Drone_AR_Flight
import platform

TIMEZONE = 'Asia/Tokyo'

class DroneUI:
    def __init__(self,drone,outputpath):
        self.drone = drone
        self.ar_cmd = 'MANUAL'
        self.ar_val = 0

        self.auto_pilot = False
        self.takeoff = False
        self.distance = 20
        self.degree = 10
        self.FRAME_W = 960
        self.FRAME_H = 720

        self.now_battery = int(0)
        self.now_height = int(0)

        self.drone_ar = Drone_AR_Flight()
        self.frame_no = 0
        self.frame_lock = threading.Lock()
        self.blank_frame = np.zeros((self.FRAME_H, self.FRAME_W, 3), np.uint8)
        self.frame = self.blank_frame
        
        self.root = tki.Tk()
        self.image = Image.fromarray(self.frame)
        self.image = ImageTk.PhotoImage(self.image)
        self.panel = tki.Label(image=self.image)
        self.panel.image = self.image
        self.panel.pack(side="left", padx=10, pady=10)

        self.text1 = tki.Label(self.root, text=
                          'W - Up\t\tArrow U - Forward\n'
                          'S - Down\t\tArrow D - Backward\n'
                          'A - Rotate Left\tArrow L - Left\n'
                          'D - Rotate Right\tArrow R - Right\n',
                          justify="left")
        self.text1.pack(side="top")

        self.battery_str = tki.StringVar()
        self.battery_str.set('Battery : ')
        self.battery_indicate = tki.Label(textvariable=self.battery_str, width=15, anchor=tki.W, justify='left',
                                          foreground='#ffffff', background='#000000', font=("",16))
        self.battery_indicate.pack(fill="both", anchor=tki.W)

        self.height_str = tki.StringVar()
        self.height_str.set('Altitude : ')
        self.height_indicate = tki.Label(textvariable=self.height_str, width=15, anchor=tki.W, justify='left',
                                         foreground='#ffffff', background='#0000a0', font=("",16))
        self.height_indicate.pack(fill="both", anchor=tki.W)

        self.barcode_str = tki.StringVar()
        self.barcode_str.set('')
        self.barcode_indicate = tki.Label(textvariable=self.barcode_str, width=15, anchor=tki.W, justify='left',
                                          foreground='#000000', background='#ffffff', font=("",16))
        self.barcode_indicate.pack(fill="both", anchor=tki.W)
        self.barcode_latest_str = ''

        self.btn_landing = tki.Button(
            self.root, text="Land", relief="raised", command=self.droneLanding)
        self.btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            self.root, text="Takeoff", relief="raised", command=self.droneTakeOff)
        self.btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            self.root, text="Auto pilot", relief="raised", command=self._autoPilot)
        self.btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.tmp_f = tki.Frame(self.root, width=100, height=2)
        self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        self.hist_txt = tki.Text(self.root, height=16, width=40)
        self.hist_txt.pack(side='bottom', fill='both', expand='yes', padx=10, pady=5)

        self.root.wm_title("Drone UI")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        self.video_thread_stop = threading.Event()
        self.video_thread = threading.Thread(target=self._video_loop, args=())
        self.video_thread.daemon = True
        self.video_thread.start()

        self.get_GUI_Image_thread_stop = threading.Event()
        self.get_GUI_Image_thread = threading.Thread(target = self._getGUIImage)
        self.get_GUI_Image_thread.daemon = True
        self.get_GUI_Image_thread.start()

        self.sending_command_thread_stop = threading.Event()
        self.sending_command_thread = threading.Thread(target = self._sendingCommand)
        self.sending_command_thread.daemon = True
        self.sending_command_thread.start()

        self._add_log('apli boot')

    def _video_loop(self):
        time.sleep(0.5)
        while not self.video_thread_stop.is_set():
            if hasattr(self.drone, 'read'):
                self.frame_lock.acquire()
                try:
                    self.frame = self.drone.read_video_frame()
                except:
                    print('Err : caught a RuntimeError')
                self.frame_lock.release()
            time.sleep(0.011)
        
        return

    def _getGUIImage(self):
        while not self.get_GUI_Image_thread_stop.is_set():
            if hasattr(self.drone, 'read_video_frame'):
                self.frame_lock.acquire()
                try:
                    self.frame = self.drone.read_video_frame()
                except:
                    print('Err : caught a RuntimeError')
                self.frame_lock.release()

            if self.frame is None or self.frame.size == 0:
                continue

            if self.frame.shape[1] != 960:
                continue

            if self.get_GUI_Image_thread_stop.is_set():
                break

            self.frame_lock.acquire()
            self.drone_ar.renew_frame(self.frame, self.frame_no, self.now_height, self.ar_cmd, self.ar_val)
            self.frame_no += 1
            self.image = Image.fromarray(self.frame)
            self.drone_ar.draw_txt(self.image, self.ar_cmd, self.ar_val)
            self.frame_lock.release()

            self.image = ImageTk.PhotoImage(self.image)
            self.panel.configure(image=self.image)
            self.panel.image = self.image
            time.sleep(0.033)
        
        return

    def _sendingCommand(self):
        poling_counter = 0
        while not self.sending_command_thread_stop.is_set():
            if self.takeoff and (poling_counter % 12) == 0 and self.auto_pilot: # and toggle == 0:
                self.ar_cmd, self.ar_val = self.drone_ar.get_command()
                if self.ar_cmd== 'up':
                    self.droneUp(self.ar_val)
                elif self.ar_cmd == 'down':
                    self.droneDown(self.ar_val)
                elif self.ar_cmd == 'forward':
                    self.droneMoveForward(self.ar_val)
                elif self.ar_cmd == 'back':
                    self.droneMoveBackward(self.ar_val)
                elif self.ar_cmd == 'left':
                    self.droneMoveLeft(self.ar_val)
                elif self.ar_cmd == 'right':
                    self.droneMoveRight(self.ar_val)
                elif self.ar_cmd == 'rotateLeft':
                    self.droneCCW(self.ar_val)
                elif self.ar_cmd == 'rotateRight':
                    self.droneCW(self.ar_val)
                elif self.ar_cmd == 'stay':
                    print('>> stay')
               
            tmpstr = self.drone_ar.get_latest_barcode()
            if self.barcode_latest_str != tmpstr:
                self.barcode_latest_str = tmpstr
                self.barcode_str.set(tmpstr)
                self._add_log(tmpstr)

            self.get_battery()
            self.get_height()
            poling_counter += 1
            time.sleep(0.3)
        
        return

    def droneTakeOff(self):
        takeoff_response = None
        self.drone.set_speed(75)
        time.sleep(0.2)
        self.drone.takeoff()
        time.sleep(0.2)
        self.takeoff = True
        return

    def droneLanding(self):
        self.takeoff = False
        self.drone.land()
        time.sleep(0.2)
        return

    def _autoPilot(self):
        if self.auto_pilot:
            self.ar_cmd = 'MANUAL'
            self.auto_pilot = False
        else:
            self.auto_pilot = True
        return

    def droneCW(self, degree):
        self.drone.rotate_cw(degree)
        return

    def droneCCW(self, degree):
        self.drone.rotate_ccw(degree)
        return

    def droneMoveForward(self, distance):
        self.drone.move_forward(distance)
        return

    def droneMoveBackward(self, distance):
        self.drone.move_backward(distance)
        return

    def droneMoveLeft(self, distance):
        self.drone.move_left(distance)
        return

    def droneMoveRight(self, distance):
        self.drone.move_right(distance)
        return

    def droneUp(self, dist):
        self.drone.move_up(dist)
        return

    def droneDown(self, dist):
        self.drone.move_down(dist)
        return

    def on_keypress_w(self, event):
        self.distance = 20
        print('Up %d cm' % self.distance)
        self.droneUp(self.distance)
        return

    def on_keypress_s(self, event):
        self.distance = 20
        print('Down %d cm' % self.distance)
        self.droneDown(self.distance)
        return

    def on_keypress_a(self, event):
        self.degree = 10
        print('Rotate left %d degree' % self.degree)
        self.droneCCW(self.degree)
        return

    def on_keypress_d(self, event):
        self.degree = 10
        print('Rotate right %d m' % self.degree)
        self.droneCW(self.degree)
        return

    def on_keypress_up(self, event):
        self.distance = 20
        print('forward %d cm' % self.distance)
        self.droneMoveForward(self.distance)
        return

    def on_keypress_down(self, event):
        self.distance = 20
        print('backward %d cm' % self.distance)
        self.droneMoveBackward(self.distance)
        return

    def on_keypress_left(self, event):
        self.distance = 20
        print('left %d cm' % self.distance)
        self.droneMoveLeft(self.distance)
        return

    def on_keypress_right(self, event):
        self.distance = 20
        print('right %d cm' % self.distance)
        self.droneMoveRight(self.distance)
        return

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()
        return

    def get_battery(self):
        self.now_battery = int(self.drone.get_battery())
        str_val = 'Battery : ' + str(self.now_battery) + ' [%]'
        self.battery_str.set(str_val)
        return

    def get_height(self):
        int_val = self.drone.get_height()
        if int_val != 0:
            int_val *=10
            if abs(int_val - self.now_height) < 100:
                self.now_height = int_val

        str_val = 'Altitude : ' + str(self.now_height) + ' [cm]'
        self.height_str.set(str_val)
        return

    def onClose(self):
        print('closing 1...')
        self.sending_command_thread_stop.set()
        self.sending_command_thread.join(1)
        if self.sending_command_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 2...')
        self.video_thread_stop.set()
        self.video_thread.join(1)
        if self.video_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 3...')
        self.get_GUI_Image_thread_stop.set()
        self.get_GUI_Image_thread.join(1)
        if self.get_GUI_Image_thread.is_alive():
            print('sys exit()...')
            sys.exit()

        print('closing 4...')
        self.drone.close()
        del self.drone
        self.root.quit()
        return

    def _add_log(self, arg_log):
        now = datetime.datetime.now(pytz.timezone(TIMEZONE))
        nowtimestr = str(now.strftime('%X'))
        logstr = nowtimestr + ' : [' + arg_log + ']\n'
        self.hist_txt.insert(tki.END, logstr)
        
        f = open('detect_ar.csv','a')
        writeline = nowtimestr + ',' + arg_log + ',\n'
        f.write(writeline)
        f.close()

        return

#eof

