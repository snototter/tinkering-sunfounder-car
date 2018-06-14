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
  #btn_thumb right
  # btn_top left
                }
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
            if event.code in type_map:
                type_map[event.code](event.state)
            else:
                print('  Unmapped CODE: {}, {}, {}'.format(event.ev_type, event.code, event.state))
        else:
            print('  Unmapped EV_TYPE: {}, {}, {}'.format(event.ev_type, event.code, event.state))

    def map_analog_value(self, state, callback_handle):
        '''Maps the analog stick values to binary states required for the req_* method'''
        pass

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
    

def main():
    car_ctrl = GamepadController()
    car_ctrl.handle_events()


if __name__ == "__main__":
    main()
