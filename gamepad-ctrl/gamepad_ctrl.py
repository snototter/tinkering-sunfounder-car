#!/usr/bin/env python

import car_controller as ctrl
import sys

# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

# Make util
def enum(**enums):
    return type('Enum', (), enums)

"""Backward compatible enums for valid system states"""
DrivingState = enum(STOPPED=1, FORWARD=2, BACKWARD=3)
SteeringState = enum(STRAIGHT=1, LEFT=2, RIGHT=3)

class GamepadController:
    """Controlling the RaspberryPi-powered car via a gamepad."""
    def __init__(self):
        #self.controller = ctrl.TcpCarController()
        self.controller = ctrl.DummyCarController()
        # Event mapping for our CSL Generic Gamepad
        self.event_mapping = {
            'Key' : {
                'BTN_TRIGGER' : self.req_fwd,
                'BTN_THUMB2' : self.req_bwd,
                'BTN_THUMB' : self.req_right,
                'BTN_TOP' : self.req_left,
                },
            'Absolute' : {
                'ABS_RZ' : self.req_driving_stick255,
                'ABS_RX' : self.req_steering_stick255,
                #'ABS_Y' :
                #'ABS_RZ' : (self.req_fwd, -1, 255), # values less than the middle (127-131) indicate that we should move forward (we'll check the sign)
                #TODO self.req_driving_stick255 (instead of tuple) map 0-0.45 to fwd, 0.45-0.55 to stop, 0.55+ to backward
                },
            # Dummy mappings to avoid spamming the logs while testing the events triggered by our gamepad
            'Sync' : { 'SYN_REPORT' : self.req_ignore },
            'Misc' : { 'MSC_SCAN' : self.req_ignore }
            }
# Add Absolute - map 0..127..255 to -1 0 1, pass to move_fwd()
        # We need to keep track of the servo states programmatically for now, to avoid killing the servos
        self.states = {
            'drive' : DrivingState.STOPPED,
            'steering' : SteeringState.STRAIGHT,
        }
#Add button to home&stop all


    def handle_events(self):
        try:
            while True:
                events = get_gamepad()
                for event in events:
                    self.process_event(event)
        except KeyboardInterrupt:
            # Quit
            pass

    def process_event(self, event):
        if event.ev_type in self.event_mapping:
            # ev_type == analog ? map value to true/false according to the mapped req_* callback
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
    #     '''Maps the analog stick values to binary states required for the req_* method'''
    #     # TODO parametrize: our stick isn't perfectly centered and flips between 125--131 at the center position, thus, we require a minimum offset of ~10 %
    #     if desired_sign < 0:
    #         return value < 0.45 * max_value
    #     else:
    #         return value > 0.55 * max_value

    def req_driving_stick255(self, event_value):
        # Driving = fwd, stop, back; depending on axis position (allow noisy readings of the axis)
        # We use the right axis which returns event codes from 0..255
        if event_value < 0.45*255:
            self.req_drive(self.controller.drive_forward, DrivingState.FORWARD, True)
        elif event_value < 0.55*255:
            self.req_stop_driving()
        else:
            self.req_drive(self.controller.drive_backward, DrivingState.BACKWARD, True)

    def req_drive(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state. Otherwise, stop moving. Leveraged by our req_fwd/bwd request handlers."""
        if event_value:
            if self.states['drive'] != desired_state:
                # If moving in the opposite direction, stop the motor first.
                if self.states['drive'] != DrivingState.STOPPED:
                    self.req_stop_driving()
                # Try to start moving in the requested direction.
                if ctrl_callback():
                    self.states['drive'] = desired_state
                else:
                    # TODO Raise exception
                    pass
        else:
            if self.states['drive'] == desired_state:
                self.req_stop_driving()

    def req_fwd(self, value):
        self.req_drive(self.controller.drive_forward, DrivingState.FORWARD, value)

    def req_bwd(self, value):
        self.req_drive(self.controller.drive_backward, DrivingState.BACKWARD, value)

    def req_stop_driving(self):
        if self.controller.stop_driving():
            self.states['drive'] = DrivingState.STOPPED
        else:
            # TODO Raise exception
            pass

    def req_steering_stick255(self, event_value):
        # Steering = left, straight, right; depending on axis position (allow noisy readings of the axis)
        if event_value < 0.45*255:
            self.req_steering(self.controller.steer_left, SteeringState.LEFT, True)
        elif event_value < 0.55*255:
            self.req_steer_straight()
        else:
            self.req_steering(self.controller.steer_right, SteeringState.RIGHT, True)

    def req_steering(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state. Otherwise, steer straight ahead. Leveraged by our req_left/right request handlers."""
        if event_value:
            if self.states['steering'] != desired_state:
                # If moving in the opposite direction, stop the motor first.
                if self.states['steering'] != SteeringState.STRAIGHT:
                    self.req_steer_straight()
                # Try to start moving in the requested direction.
                if ctrl_callback():
                    self.states['steering'] = desired_state
                else:
                    # TODO Raise exception
                    pass
        else:
            if self.states['steering'] == desired_state:
                self.req_steer_straight()

    def req_left(self, value):
        self.req_steering(self.controller.steer_left, SteeringState.LEFT, value)

    def req_right(self, value):
        self.req_steering(self.controller.steer_right, SteeringState.RIGHT, value)

    def req_steer_straight(self):
        if self.controller.steer_straight():
            self.states['steering'] = SteeringState.STRAIGHT
        else:
            # TODO raise exception
            pass

    def req_ignore(self, value):
        """Do nothing"""
        pass


def main():
    car_ctrl = GamepadController()
    car_ctrl.handle_events()


if __name__ == "__main__":
    main()
