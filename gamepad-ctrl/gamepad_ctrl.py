#!/usr/bin/env python

import sys

# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

class CarController:
    def move_forward(self):
        print('Moving forward')
    def stop_moving(self):
        print('Stop moving')
    def move_backward(self):
        print('Moving backward')

def enum(**enums):
    return type('Enum', (), enums)

DrivingState = enum(STOPPED=1, FORWARD=2, BACKWARD=3)
SteeringState = enum(STRAIGHT=1, LEFT=2, RIGHT=3)

class GamepadCarController(CarController):

    def __init__(self):
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
            

    def listen_for_events(self):
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
        """Invoke the given control callback if we're not in the desired state. Otherwise, stop moving."""
        if event_value:
            if self.states['drive'] != desired_state:
                if ctrl_callback():
                    self.states['drive'] = desired_state
                else:
                    # Raise exception
                    pass
            else:
                print('already moving')
        else:
            if self.states['drive'] == desired_state:
                self.stop_moving()
                self.states['drive'] = self.DriveState.STOPPED

    def req_fwd(self, value):
        req_drive(self.move_forward, DrivingState.FORWARD, value)

    def req_bwd(self, value):
        req_drive(self.move_forward, DrivingState.BACKWARD, value)
    
#    def req_fwd(self, state):
#        '''Event to move forward (or stop moving forward) has been triggered'''
#        if state:
#            if self.states['drive'] != DriveState.FORWARD
#                print('moving forward....{}'.format(state))
#                self.move_forward()
#                self.states['drive'] = DriveState.FORWARD
#            else:
#                print('already moving fwd')
#        else:
#            if self.states['drive'] == DriveState.FORWARD:
#                print('stop moving fwd')
#                self.stop_moving()
#                self.states['drive'] = self.DriveState.STOPPED

def main():
    car_ctrl = GamepadCarController()
    car_ctrl.listen_for_events()


if __name__ == "__main__":
    main()
