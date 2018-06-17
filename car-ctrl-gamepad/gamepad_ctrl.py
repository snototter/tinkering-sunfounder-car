#!/usr/bin/env python

#TODO add cd to python path https://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory
import argparse
import car_controller as ctrl
import sys
# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

# TODO Make util
def enum(**enums):
    return type('Enum', (), enums)

"""Backward compatible enums for valid system states"""
DrivingState = enum(STOPPED=1, FORWARD=2, BACKWARD=4)
SteeringState = enum(STRAIGHT=1, LEFT=2, RIGHT=4)


# TODO parametrize initialization of GamepadController
# Dict Key/Absolute : { event/button code : Driving/Steering/... enum }
# TODO Should we rename it? Key = Button, Absolute = Joystick ?
# TODO add param stick_jittering_rejection (percentage)
def get_csl_generic_gamepad_config():
    """Exemplary config for our CSL Generic Gamepad"""
    gamepad_config = { 
        'Key' : {
            'BTN_TRIGGER' : DrivingState.FORWARD, 
            'BTN_THUMB2' : DrivingState.BACKWARD,
            'BTN_THUMB' : SteeringState.RIGHT,
            'BTN_TOP' : SteeringState.LEFT,
            },
        'Absolute' : {
            # TODO config_value & (FWD | BWD)
            # we need the axis range, though!
            'ABS_RZ' : [] 
            },
        }
    return gamepad_config

class GamepadController:
    """Controlling the RaspberryPi-powered car via a gamepad."""
    def __init__(self, controller):
        self.controller = controller
        self.step_size_speed = 10 # dec/inc speed by X
        self.speed_range = [1, 100] # min/max possible speed
        # Event mapping for our CSL Generic Gamepad
        self.event_mapping = {
            'Key' : {
                'BTN_TRIGGER' : self.__req_fwd,
                'BTN_THUMB2' : self.__req_bwd,
                'BTN_THUMB' : self.__req_right,
                'BTN_TOP' : self.__req_left,
                'BTN_TOP2' : self.__req_speedup,
                'BTN_BASE' : self.__req_slowdown,
                'BTN_BASE3' : self.__req_stop_all,
                'BTN_BASE4' : self.__req_home_all,
                },
            'Absolute' : {
                'ABS_RZ' : self.__req_driving_stick255,
                'ABS_RX' : self.__req_steering_stick255,
                #'ABS_Y' :
                #'ABS_RZ' : (self.__req_fwd, -1, 255), # values less than the middle (127-131) indicate that we should move forward (we'll check the sign)
                #TODO self.__req_driving_stick255 (instead of tuple) map 0-0.45 to fwd, 0.45-0.55 to stop, 0.55+ to backward
                },
            # Dummy mappings to avoid spamming the logs while testing the events triggered by our gamepad
            'Sync' : { 'SYN_REPORT' : self.__req_ignore },
            'Misc' : { 'MSC_SCAN' : self.__req_ignore }
            }
        # We need to keep track of the servo states programmatically for now, to avoid killing the servos
        self.states = {
            'drive' : DrivingState.STOPPED,
            'steering' : SteeringState.STRAIGHT,
            'speed' : 20,
        }
        # Stop motors, home all servos, reset speed
        self.controller.stop_all()
        self.controller.home_all()
        self.controller.set_speed(self.states['speed'])


    def handle_events(self):
        try:
            while True:
                events = get_gamepad()
                for event in events:
                    self.__process_event(event)
        except KeyboardInterrupt:
            # Quit
            pass

    def __process_event(self, event):
        if event.ev_type in self.event_mapping:
            # ev_type == analog ? map value to true/false according to the mapped __req_* callback
            # Otherwise, just pass the event state as is.
            type_map = self.event_mapping[event.ev_type]
            #if type(type_map) is tuple:
            # if event.ev_type == 'Absolute':
            #     if event.code in type_map:
            #         # We need to map the stick values 0...max_axis to True/False - thus, our event/function mapping contains a tuple
            #         fhandle, sgn, max_axis = type_map[event.code]
            #         # Map the absolute value to boolean flag
            #         bvalue = self.map_absolute_value(event.state, sgn, max_axis)
            #         # Process request as usual:
            #         fhandle(bvalue)
            #     else:
            #         print('  Unmapped CODE: {}, {}, {}'.format(event.ev_type, event.code, event.state))
            # else:
            if event.code in type_map:
                type_map[event.code](event.state)
            else:
                print('  Unmapped CODE: {}, {}, {}'.format(event.ev_type, event.code, event.state))
        else:
            print('  Unmapped EV_TYPE: {}, {}, {}'.format(event.ev_type, event.code, event.state))

    # def map_absolute_value(self, value, desired_sign, max_value):
    #     '''Maps the analog stick values to binary states required for the __req_* method'''
    #     # TODO parametrize: our stick isn't perfectly centered and flips between 125--131 at the center position, thus, we require a minimum offset of ~10 %
    #     if desired_sign < 0:
    #         return value < 0.45 * max_value
    #     else:
    #         return value > 0.55 * max_value

    def __req_driving_stick255(self, event_value):
        # Driving = fwd, stop, back; depending on axis position (allow noisy readings of the axis)
        # We use the right axis which returns event codes from 0..255
        if event_value < 0.45*255:
            self.__req_drive(self.controller.drive_forward, DrivingState.FORWARD, True)
        elif event_value < 0.55*255:
            self.__req_stop_driving()
        else:
            self.__req_drive(self.controller.drive_backward, DrivingState.BACKWARD, True)

    def __req_drive(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state. Otherwise, stop moving. Leveraged by our __req_fwd/bwd request handlers."""
        if event_value:
            if self.states['drive'] != desired_state:
                # If moving in the opposite direction, stop the motor first.
                if self.states['drive'] != DrivingState.STOPPED:
                    self.__req_stop_driving()
                # Try to start moving in the requested direction.
                if ctrl_callback():
                    self.states['drive'] = desired_state
                else:
                    # TODO Raise exception
                    pass
        else:
            if self.states['drive'] == desired_state:
                self.__req_stop_driving()

    def __req_fwd(self, value):
        self.__req_drive(self.controller.drive_forward, DrivingState.FORWARD, value)

    def __req_bwd(self, value):
        self.__req_drive(self.controller.drive_backward, DrivingState.BACKWARD, value)

    def __req_stop_driving(self):
        if self.controller.stop_driving():
            self.states['drive'] = DrivingState.STOPPED
        else:
            # TODO Raise exception
            pass

    def __req_steering_stick255(self, event_value):
        # Steering = left, straight, right; depending on axis position (allow noisy readings of the axis)
        if event_value < 0.45*255:
            self.__req_steering(self.controller.steer_left, SteeringState.LEFT, True)
        elif event_value < 0.55*255:
            self.__req_steer_straight()
        else:
            self.__req_steering(self.controller.steer_right, SteeringState.RIGHT, True)

    def __req_steering(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state. Otherwise, steer straight ahead. Leveraged by our __req_left/right request handlers."""
        if event_value:
            if self.states['steering'] != desired_state:
                # If moving in the opposite direction, stop the motor first.
                if self.states['steering'] != SteeringState.STRAIGHT:
                    self.__req_steer_straight()
                # Try to start moving in the requested direction.
                if ctrl_callback():
                    self.states['steering'] = desired_state
                else:
                    # TODO Raise exception
                    pass
        else:
            if self.states['steering'] == desired_state:
                self.__req_steer_straight()

    def __req_left(self, value):
        self.__req_steering(self.controller.steer_left, SteeringState.LEFT, value)

    def __req_right(self, value):
        self.__req_steering(self.controller.steer_right, SteeringState.RIGHT, value)

    def __req_steer_straight(self):
        if self.controller.steer_straight():
            self.states['steering'] = SteeringState.STRAIGHT
        else:
            # TODO raise exception
            pass

    def __req_setspeed(self, speed_value):
        # TODO check values with car firmware
        if speed_value >= 0 and speed_value <= 100:
            if self.controller.set_speed(speed_value):
                self.states['speed'] = speed_value
            else:
                # TODO raise exception
                pass
        else:
            # TODO raise exception
            pass

    def __req_speedup(self, event_value):
        if event_value: # If button is pressed down (inc. speed once, don't react to released button)
          spd = self.states['speed']
          if spd + self.step_size_speed <= self.speed_range[1]:
              spd = spd + self.step_size_speed
              self.__req_setspeed(spd)
    
    def __req_slowdown(self, event_value):
        if event_value: # If button is pressed down (dec. speed once, don't react to released button)
          spd = self.states['speed']
          if spd - self.step_size_speed > self.speed_range[0]:
              spd = spd - self.step_size_speed
              self.__req_setspeed(spd)


    def __req_stop_all(self, event_value):
        if event_value:
            # TODO implement
            print('Stop all')

    def __req_home_all(self, event_value):
        if event_value:
            self.__req_stop_all(True)
            # TODO implement
            print('Home all servos')

    def __req_ignore(self, value):
        """Do nothing"""
        pass


#def main():
#    car_ctrl = GamepadController()
#    car_ctrl.handle_events()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--runon', action='store', choices=['pi','tcp','dummy'],
                      help='Run local on Pi, connect via TCP to sunfounders car server, or prefer dummy debug output')
    args = parser.parse_args()
    if args.runon == 'pi':
        print('Loading Sunfounder GPIO controller')
        import sunfounder_pi_car_controller as pi_ctrl
        ctrl = pi_ctrl.GpioCarController()
    elif args.runon == 'tcp':
        print('Connecting to tcp server')
        import sunfounder_tcp_car_controller as tcp_ctrl
        ctrl = tcp_ctrl.TcpCarController()
    else:
        print('Using dummy car controller')
        ctrl = ctrl.DummyCarController()
    car_ctrl = GamepadController(ctrl)
    car_ctrl.handle_events()
