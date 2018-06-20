#!/usr/bin/env python

#TODO add cd to python path https://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory
import argparse
import car_controller as ctrl
import sys
# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

import multiprocessing
#from threading import Thread
import image_publisher

# TODO Make util
def enum(**enums):
    return type('Enum', (), enums)

"""Backward compatible enums for valid system states"""
DrivingState = enum(STOPPED=1, FORWARD=2, BACKWARD=4)
SteeringState = enum(STRAIGHT=1, LEFT=2, RIGHT=4)


# TODO list:
# * Parametrization of the GamepadController with separate configs would be
#   nice; but this requires that we map from some public config enums to the
#   internal method handles in the constructor
# * Replace Sunfounder's demo utils by more specialized (e.g. where we can turn
#   the pan/tilt unit by smaller steps)

class GamepadController:
    """Controlling the RaspberryPi-powered car via a gamepad."""
    def __init__(self, controller):
        self.controller = controller
        self.step_size_speed = 10 # dec/inc speed by X
        self.speed_range = [1, 100] # min/max possible speed
        self.pan_range = [-6, 10] # Allow +/- X "steps" of the pan servo (there's no finetuning of the pan angle yet...)
        self.tilt_range = [-10, 2]
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
                'BTN_PINKIE' : self.__req_home_pan_tilt,
                },
            'Absolute' : {
                'ABS_RZ' : self.__req_driving_stick255,
                'ABS_RX' : self.__req_steering_stick255,
                'ABS_X' : self.__req_pan_stick255,
                'ABS_Y' : self.__req_tilt_stick255,
                },
            # Dummy mappings to avoid spamming the logs while testing the events triggered by our gamepad
            'Sync' : { 'SYN_REPORT' : self.__req_ignore },
            'Misc' : { 'MSC_SCAN' : self.__req_ignore }
            }
        # We need to keep track of the servo states programmatically for now, to avoid killing the servos
        self.states = {
            'drive' : DrivingState.STOPPED,
            'steering' : SteeringState.STRAIGHT,
            'speed' : 40,
            'pan_step' : 0,
            'tilt_step' : 0,
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
            print('[I] Terminated by keyboard interrupt')
        except UnpluggedError:
            print('[E] No gamepad plugged in')


    def __process_event(self, event):
        # Look up and invoke registered handler for the given gamepad event
        if event.ev_type in self.event_mapping:
            type_map = self.event_mapping[event.ev_type]
            if event.code in type_map:
                type_map[event.code](event.state)
            else:
                print('[W] Unmapped CODE: {}, {}, {}'.format(event.ev_type, event.code, event.state))
        else:
            print('[W] Unmapped EV_TYPE: {}, {}, {}'.format(event.ev_type, event.code, event.state))


    ###################################
    # Driving FWD/BWD/Stop

    def __req_drive(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state.
           Otherwise, stop moving. Leveraged by our __req_fwd/bwd request
           handlers."""
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


    def __req_driving_stick255(self, event_value):
        """Map analog stick position to ternary motor fwd/bwd/off"""
        # The analog stick measurements may slightly jitter, so we allow
        # +/-5 per cent noise at the center position before reacting to the
        # user input.
        if event_value < 0.45*255:
            self.__req_drive(self.controller.drive_forward, DrivingState.FORWARD, True)
        elif event_value < 0.55*255:
            self.__req_stop_driving()
        else:
            self.__req_drive(self.controller.drive_backward, DrivingState.BACKWARD, True)

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


    ###################################
    # Steering

    def __req_steering(self, ctrl_callback, desired_state, event_value):
        """Invoke the given control callback if we're not in the desired state.
           Otherwise, steer straight ahead. Leveraged by our __req_left/right
           request handlers."""
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

    def __req_steering_stick255(self, event_value):
        """Map analog stick to steer left/right/straigt."""
        # Steering = left, straight, right; depending on axis position (allow noisy readings of the axis)
        if event_value < 0.45*255:
            self.__req_steering(self.controller.steer_left, SteeringState.LEFT, True)
        elif event_value < 0.55*255:
            self.__req_steer_straight()
        else:
            self.__req_steering(self.controller.steer_right, SteeringState.RIGHT, True)

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

    ###################################
    # Speed control

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


    ###################################
    # Camera movement

    def __pan_left(self):
        if self.states['pan_step'] > self.pan_range[0]:
            if self.controller.pan_left():
                self.states['pan_step'] -= 1
            else:
                #TODO raise exception
                pass
        else:
            print('[W] Cannot pan left anymore')
            pass

    def __pan_right(self):
        if self.states['pan_step'] < self.pan_range[1]:
            if self.controller.pan_right():
                self.states['pan_step'] += 1
            else:
                #TODO raise exception
                pass
        else:
            print('[W] Cannot pan right anymore')
            pass

    def __tilt_up(self):
        if self.states['tilt_step'] > self.tilt_range[0]:
            if self.controller.tilt_up():
                self.states['tilt_step'] -= 1
            else:
                #TODO raise exception
                pass
        else:
            print('[W] Cannot tilt up anymore')
            pass

    def __tilt_down(self):
        if self.states['tilt_step'] < self.tilt_range[1]:
            if self.controller.tilt_down():
                self.states['tilt_step'] += 1
            else:
                #TODO raise exception
                pass
        else:
            print('[W] Cannot tilt down anymore')
            pass

    def __req_pan_stick255(self, event_value):
        #TODO in analog mode, this event will be triggered multiple times per stick touch!!
        if event_value < 0.45*255:
            self.__pan_left()
        elif event_value >= 0.55*255:
            self.__pan_right()
        #print('Current p/t step: {} / {}'.format(self.states['pan_step'], self.states['tilt_step'])) # TODO remove debug output

    def __req_tilt_stick255(self, event_value):
        #TODO in analog mode, this event will be triggered multiple times per stick touch!!
        # Sunfounder's video_dir ctrl only allows changing the pan/tilt angle by a fixed inc/dec
        if event_value < 0.45*255:
            self.__tilt_up()
        elif event_value >= 0.55*255:
            self.__tilt_down()
        #print('Current p/t step: {} / {}'.format(self.states['pan_step'], self.states['tilt_step'])) # TODO remove debug output


    def __req_stop_all(self, event_value):
        if event_value:
            if self.controller.stop_all():
                self.states['drive'] = DrivingState.STOPPED
            else:
                # TODO raise exception
                pass

    def __req_home_all(self, event_value):
        if event_value:
            # Stop motor
            self.__req_stop_all(True)
            # Steer straight
            self.__req_steer_straight()
            # Home pan/tilt unit
            self.__req_home_pan_tilt(True)

    def __req_home_pan_tilt(self, event_value):
        if event_value:
            if self.controller.home_pan_tilt():
                self.states['pan_step'] = 0
                self.states['tilt_step'] = 0
            else:
                # TODO raise Exception
                pass

    def __req_ignore(self, value):
        """Do nothing"""
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--runon', action='store', choices=['pi','tcp','dummy'],
                      help='Run local on Pi, connect via TCP to sunfounders car server, or prefer dummy debug output')
    parser.add_argument('--bt-img-srv-mac', help='MAC address of bluetooth server to push images to connected clients', action='store')
    parser.add_argument('--bt-img-srv-port', help='Port number of bluetooth server to push images to connected clients', action='store', type=int)

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

    # Start new process to publish webcam images
    if args.bt_img_srv_port is None:
        args.bt_img_srv_port = 42

    if args.bt_img_srv_mac is not None:
        img_server = image_publisher.ImagePublishingServer(args.bt_img_srv_mac,
            port=args.bt_img_srv_port, backlog=5)
        img_server_proc = multiprocessing.Process(target=img_server.run)
        img_server_proc.start()
        #img_server_thread = Thread(target=img_server.run)
        #img_server_thread.start()
    else:
        img_server = None

    # Listen for gamepad inputs
    car_ctrl.handle_events()

    # Terminate image publisher
    if img_server is not None:
        img_server.terminate()
        img_server_proc.join()
        #img_server_thread.join()
