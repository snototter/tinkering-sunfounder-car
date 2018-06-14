#!/usr/bin/env python

import sys

# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

class CarController:
    #def __init__(self):
    # store internal state    
    def move_forward(self):
        print('Moving forward')
    def stop_moving(self):
        print('Stop moving')
    def move_backward(self):
        print('Moving backward')

def enum(**enums):
    return type('Enum', (), enums)

class GamepadCarController(CarController):
    DriveState = enum(STOPPED=1, FORWARD=2, BACKWARD=3)

    def __init__(self):
        self.event_mapping = { 
            'Key' : {
                'BTN_TRIGGER' : self.req_fwd,
  #btn_thumb right
  # btn_top left
  #btn_thumb2 back
                }
            }
# Add Absolute - map 0..127..255 to -1 0 1, pass to move_fwd()
        # We need to keep track of the servo states programmatically for now, to avoid killing the servos
        self.states = {            
            'drive' : self.DriveState.STOPPED}
            

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
            type_map = self.event_mapping[event.ev_type]
            if event.code in type_map:
                type_map[event.code](event.state)
            else:
                print('  Unmapped CODE: {}, {}, {}'.format(event.ev_type, event.code, event.state))
        else:
            print('  Unmapped EV_TYPE: {}, {}, {}'.format(event.ev_type, event.code, event.state))

    def req_fwd(self, state):
        '''Event to move forward (or stop moving forward) has been triggered'''
        if state > 0:
            if self.states['drive'] in [self.DriveState.STOPPED, self.DriveState.BACKWARD]:
                print('moving forward....{}'.format(state))
                self.move_forward()
                self.states['drive'] = self.DriveState.FORWARD
            else:
                print('already moving fwd')
        else:
            if self.states['drive'] == self.DriveState.FORWARD:
                print('stop moving fwd')
                self.stop_moving()
                self.states['drive'] = self.DriveState.STOPPED


def main():
    car_ctrl = GamepadCarController()
    car_ctrl.listen_for_events()


if __name__ == "__main__":
    main()
