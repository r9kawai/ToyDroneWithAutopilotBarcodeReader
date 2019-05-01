# This source code from https://github.com/dji-sdk/Tello-Python, then amended.
# Thank you for the open source community.

from struct import Struct
import socket
import threading
import time
import numpy as np
import libh264decoder

CMD_REQ_IFRAME =(0xcc, 0x58, 0x00, 0x7c, 0x60, 0x25, 0x00, 0x00, 0x00, 0x6c, 0x95)

class Tello:
    def __init__(self, local_ip, local_port, imperial=False, command_timeout=.3, tello_ip='192.168.10.1',
                 tello_port=8889):
        self.decoder = libh264decoder.H264Decoder()
        self.command_timeout = command_timeout
        self.response = None
        self.frame = None  # numpy array BGR -- current camera output frame
        self.is_freeze = False  # freeze current camera output
        self.last_frame = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for sending cmd
        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving video stream
        self.tello_address = (tello_ip, tello_port)
        self.local_video_port = 11111  # port for receiving video stream
        self.last_height = 0
        self.last_battery = 0
        self.now_inquiry = 'non'
        self.socket.bind((local_ip, local_port))

        # thread for receiving cmd ack
        self.receive_thread_run = True
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # to receive video -- send cmd: command, streamon
        self.socket.sendto(b'command', self.tello_address)
        print ('sent: command')
        self.socket.sendto(b'streamon', self.tello_address)
        print ('sent: streamon')

        self.socket_video.bind((local_ip, self.local_video_port))

        # thread for receiving video
        self.receive_video_thread_run = True
        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()

    def close(self):
        print('Tello.close 1')
        try:
            self.socket_video.shutdown(socket.SHUT_RDWR)
            self.socket_video.close()
        except:
            print('socket_video.error')

        print('Tello.close 2')
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            print('socket_video.error')

        print('Tello.close 3')
        self.receive_thread_run = False
        self.receive_thread.join()

        print('Tello.close 4')
        self.receive_video_thread_run = False
        self.receive_video_thread.join()
    
    def read_video_frame(self):
        if self.is_freeze:
            return self.last_frame
        else:
            return self.frame

    def video_freeze(self, is_freeze=True):
        self.is_freeze = is_freeze
        if is_freeze:
            self.last_frame = self.frame

    def _receive_thread(self):
        while self.receive_thread_run == True:
            try:
                buff, ip = self.socket.recvfrom(3000)
                if buff != None:
                    self.response = self.buff.decode('utf-8')
                    print('< res ', self.response)
                    try:
                        val = int(self.response)
                    except ValueError:
                        val = -1:
                    
                    if val > 0:
                        if self.now_inquiry == 'height':
                            print('<  res height ', val)
                            self.last_height = val
                        elif self.now_inquiry == 'battery':
                            print('<  res battery ', val)
                            self.last_battery = val
                        
            except socket.error as exc:
                print ("Caught exception socket.error : %s" % exc)

        return

    def _receive_video_thread(self):
        packet_data = ""
        while self.receive_video_thread_run == True:
            try:
                res_string, ip = self.socket_video.recvfrom(2048)
                packet_data += res_string
                # end of frame
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                    packet_data = ""

            except socket.error as exc:
                print ("Caught exception socket.error : %s" % exc)
    
    def _h264_decode(self, packet_data):
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                # print 'frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls)
                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
                frame = (frame.reshape((h, ls / 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    def send_command(self, command):
        if command == 'iframe':
            s11 = Struct("!11B")
            reqifcmd = s11.pack(*CMD_REQ_IFRAME)
            print('>> send req iframe')
            self.socket.sendto(reqifcmd, self.tello_address)
        else:
            print (">> send cmd: {}".format(command))
            self.socket.sendto(command.encode('utf-8'), self.tello_address)
        return
    
    def takeoff(self):
        self.send_command('takeoff')
        return

    def set_speed(self, speed):
        self.send_command('speed %s' % speed)
        return

    def rotate_cw(self, degrees):
        self.send_command('cw %s' % degrees)
        return

    def rotate_ccw(self, degrees):
        self.send_command('ccw %s' % degrees)
        return

    def get_height(self):
        self.now_inquiry = 'height'
        self.send_command('height?')
        return self.last_height

    def get_battery(self):
        self.now_inquiry = 'battery'
        self.send_command('battery?')
        return self.last_battery

    def land(self):
        self.send_command('land')
        return

    def move(self, direction, distance):
        self.send_command('%s %s' % (direction, distance))
        return

    def move_backward(self, distance):
        self.move('back', distance)
        return

    def move_down(self, distance):
        self.move('down', distance)
        return

    def move_forward(self, distance):
        self.move('forward', distance)
        return

    def move_left(self, distance):
        self.move('left', distance)
        return

    def move_right(self, distance):
        self.move('right', distance)
        return

    def move_up(self, distance):
        self.move('up', distance)
        return

    def req_iframe(self):
        self.send_command('iframe')
        return

#eof

