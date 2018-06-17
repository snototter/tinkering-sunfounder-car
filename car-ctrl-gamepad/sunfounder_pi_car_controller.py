#!/usr/bin/env python
from car_controller import CarController

import sys
# Load sunfounder's motor/servo utils
#sys.path.append('../third_party/sunfounder/server')
sys.path.append('sunfounder-patched')
import car_dir as sfsteering
import motor as sfdriving
#import video_dir as sfpantilt

#video_dir.setup(busnum=busnum)
#car_dir.setup(busnum=busnum)
#motor.setup(busnum=busnum)     # Initialize the Raspberry Pi GPIO connected to the DC motor. 
#video_dir.home_x_y()
#car_dir.home()


class GpioCarController(CarController):
    """To be used on the pi, accesses the pins directly."""
    def __init__(self):
        self.busnum = 1
        sfdriving.setup(busnum=self.busnum)
        sfsteering.setup(busnum=self.busnum)

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
