#!/usr/bin/env python
from car_controller import CarController
import socket

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
        return True

    def drive_backward(self):
        self.tcp_client.send('backward'.encode())
        return True

    def stop_driving(self):
        self.tcp_client.send('stop'.encode())
        return True

    def steer_left(self):
        self.tcp_client.send('left'.encode())
        return True

    def steer_right(self):
        self.tcp_client.send('right'.encode())
        return True

    def steer_straight(self):
        self.tcp_client.send('home'.encode())
        return True

    def set_speed(self, speed_value):
        data = 'speed' + str(speed_value)
        self.tcp_client.send(data.encode())
        return True

# TODO 'home' home all or only steering servo???, xy_home is for pan/tilt, ... check sunfounder's server implementation
#def stop_fun(event):
#	tcpCliSock.send('stop')
#def home_fun(event):
#	tcpCliSock.send('home')
#def x_increase(event):
#	tcpCliSock.send('x+')
#def x_decrease(event):
#	tcpCliSock.send('x-')
#def y_increase(event):
#	tcpCliSock.send('y+')
#def y_decrease(event):
#	tcpCliSock.send('y-')
#def xy_home(event):
#	tcpCliSock.send('xy_home')
