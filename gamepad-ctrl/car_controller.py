#!/usr/bin/env python

from abc import ABCMeta, abstractmethod
import socket

class CarController:
    __metaclass__ = ABCMeta

    @abstractmethod
    def drive_forward(self):
        return

    @abstractmethod
    def stop_driving(self):
        return

    @abstractmethod
    def drive_backward(self):
        return

    @abstractmethod
    def steer_left(self):
        return

    @abstractmethod
    def steer_straight(self):
        return

    @abstractmethod
    def steer_right(self):
        return

    # TODO pan/tilt; home all; stop all;


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

    def __del__(self):
        # Disconnect
        if self.is_connected:
            self.tcp_client.send('stop')
            self.tcp_client.close()

    def drive_forward(self):
        self.tcp_client.send('forward')
        return True

    def drive_backward(self):
        self.tcp_client.send('backward')
        return True

    def stop_driving(self):
        self.tcp_client.send('stop')
        return True

    def steer_left(self):
        self.tcp_client.send('left')
        return True

    def steer_right(self):
        self.tcp_client.send('right')
        return True

    def steer_straight(self):
        self.tcp_client.send('home')
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


class LocalCarController(CarController):
    """To be used on the pi, accesses the pins directly."""
    pass

class DummyCarController(CarController):
    """Used to debug without pi running"""
    def drive_forward(self):
        print('MV Forward')
        return True

    def drive_backward(self):
        print('MV Backward')
        return True

    def stop_driving(self):
        print('MV Motors stopped')
        return True

    def steer_left(self):
        print('ST Left')
        return True

    def steer_right(self):
        print('ST Right')
        return True

    def steer_straight(self):
        print('ST Straight')
        return True
