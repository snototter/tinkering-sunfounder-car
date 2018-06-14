#!/usr/bin/env python

from abc import ABCMeta, abstractmethod

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

    def steer_straight(self):
        return


class TcpCarController(CarController):
    """Connects to the Sunfounder TCP client"""
    pass

class LocalCarController(CarController):
    """To be used on the pi, accesses the pins directly."""
    pass

class DummyCarController(CarController):
    """Used to debug without pi running"""
    def drive_forward(self):
        print('Forward')
        return True

    def drive_backward(self):
        print('Backward')
        return True

    def stop_driving(self):
        print('Motors stopped')
        return True

    def steer_left(self):
        print('Left')
        return True

    def steer_right(self):
        print('Right')
        return True

