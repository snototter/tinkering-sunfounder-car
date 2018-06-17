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

    @abstractmethod
    def steer_straight(self):
        return

    @abstractmethod
    def steer_right(self):
        return

    @abstractmethod
    def set_speed(self, speed_value):
        return

    def stop_all(self):
        self.stop_driving()

    def home_all(self):
        self.stop_all()
        self.steer_straight()
#TODO        self.pan(0)

    # TODO pan/tilt; home all; stop all;


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

    def set_speed(self, speed_value):
        print('Setting speed to {}'.format(speed_value))
        return True

