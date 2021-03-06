#!/usr/bin/env python
from car_controller import CarController

import sys
# Load sunfounder's motor/servo utils (patched for python3)
sys.path.append('sunfounder-patched')
import car_dir as sfsteering
import motor as sfdriving
import video_dir as sfpantilt


class GpioCarController(CarController):
    """To be used on the pi, accesses the pins directly."""
    def __init__(self):
        self.busnum = 1 # See sunfounder's documentation, should be 1 for RPi3
        sfdriving.setup(busnum=self.busnum)
        sfsteering.setup(busnum=self.busnum)
        sfpantilt.setup(busnum=self.busnum)

    def drive_forward(self):
        sfdriving.forward()
        return True

    def drive_backward(self):
        sfdriving.backward()
        return True

    def stop_driving(self):
        sfdriving.ctrl(0)
        return True

    def steer_left(self):
        sfsteering.turn_left()
        return True

    def steer_right(self):
        sfsteering.turn_right()
        return True

    def steer_straight(self):
        sfsteering.home()
        return True

    def set_speed(self, speed_value):
        if speed_value < 24:
            speed_value = 24
        sfdriving.setSpeed(speed_value)
        return True

    def pan_left(self):
        sfpantilt.move_decrease_x()
        return True

    def pan_right(self):
        sfpantilt.move_increase_x()
        return True

    def tilt_up(self):
        sfpantilt.move_increase_y()
        return True

    def tilt_down(self):
        sfpantilt.move_decrease_y()
        return True

    def home_pan_tilt(self):
        sfpantilt.home_x_y()
        return True
