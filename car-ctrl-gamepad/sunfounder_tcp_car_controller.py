#!/usr/bin/env python
from car_controller import CarController
import socket
import time

class TcpCarController(CarController):
    """Connects to the Sunfounder TCP server."""
    def __init__(self):
        # TODO parameter: config
        # Connect to the car's TCP server:
        self.is_connected = False
        self.host = '192.168.0.31'
        self.port = 21567
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((self.host, self.port))
        self.is_connected = True
        print('Connected to car server on {}:{}'.format(self.host, self.port))

    def __del__(self):
        # Disconnect
        if self.is_connected:
            self.tcp_client.send('stop'.encode())
            self.tcp_client.close()

    def drive_forward(self):
        self.tcp_client.send('forward'.encode())
        time.sleep(0.1)
        return True

    def drive_backward(self):
        self.tcp_client.send('backward'.encode())
        time.sleep(0.1)
        return True

    def stop_driving(self):
        self.tcp_client.sendall('stop'.encode())
        time.sleep(0.1)
        return True

    def steer_left(self):
        self.tcp_client.send('left'.encode())
        time.sleep(0.1)
        return True

    def steer_right(self):
        self.tcp_client.send('right'.encode())
        time.sleep(0.1)
        return True

    def steer_straight(self):
        self.tcp_client.send('home'.encode())
        time.sleep(0.1)
        return True

    def set_speed(self, speed_value):
        data = 'speed' + str(speed_value)
        self.tcp_client.send(data.encode())
        time.sleep(0.1)
        return True

    def pan_left(self):
        self.tcp_client.send('x-'.encode())
        time.sleep(0.1)
        return True

    def pan_right(self):
        self.tcp_client.send('x+'.encode())
        time.sleep(0.1)
        return True

    def tilt_up(self):
        self.tcp_client.send('y+'.encode())
        time.sleep(0.1)
        return True

    def tilt_down(self):
        self.tcp_client.send('y-'.encode())
        time.sleep(0.1)
        return True

    def home_pan_tilt(self):
        self.tcp_client.send('xy_home'.encode())
        time.sleep(0.1)
        return True

