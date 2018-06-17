#!/usr/bin/env python
from car_controller import CarController

import sys
# Load sunfounder's motor/servo utils
sys.path.append('../third_party/sunfounder/server')
import car_dir as sfsteering
import motor as sfdriving
import video_dir as sfpantilt


class SunfounderCarController(CarController):
    """To be used on the pi, accesses the pins directly."""
    # use sfsteering, sfdriving, sfpantilt
    pass
