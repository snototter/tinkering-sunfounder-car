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
        self.is_connected = False
        self.host = '192.168.0.31'
        self.port = 21567
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((self.host, self.port))
        self.is_connected = True

    def __del__(self):
        if self.is_connected:
            self.tcp_client.send('stop')
            self.tcp_client.close()


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
