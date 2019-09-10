#!/usr/bin/env python

import argparse
import socket
import io
# from PIL import Image
# import cv2
# import numpy as np
import threading
import time


# import getch
import curses
 

if __name__ == "__main__":
    srv = '127.0.0.1'
    port = 8080
    print('[I] Connecting to "{:s}":{:d}'.format(srv, port))
#         sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((srv, port))

    # get the curses screen window
    screen = curses.initscr()
    # turn off input echoing
    curses.noecho()
    # respond to keys immediately (don't wait for enter)
    curses.cbreak()
    # map arrow keys to special values
    screen.keypad(True)

    speed = 20
    try:
        bwd = False
        while True:
            k = screen.getch()

            stop = False
            left, right = False, False # only steer while pressing the button
            if k == ord('f'):
                speed = min(100, speed + 10)
                screen.addstr(0, 0, 'faster {:d}'.format(speed))
            elif k == ord('s'):
                speed = max(1, speed - 10)
                screen.addstr(0, 0, 'slower {:d}'.format(speed))
            elif k == ord('d') or k == ord('q'):
                screen.addstr(0, 0, 'STOP')
                stop = True
            elif k == curses.KEY_RIGHT:
                right = True
            elif k == curses.KEY_LEFT:
                # screen.addstr(0, 0, 'left')
                left = True
            elif k == curses.KEY_UP:
                bwd = False
            elif k == curses.KEY_DOWN:
                bwd = True
                # screen.addstr(0, 0, 'down/bwd')

            if stop:
                sock.send('q'.encode('utf-8'))
            else:
                cmd = '{}{}{}'.format('f' if not bwd else 'b',
                    's' if not left and not right else ('l' if left else 'r'),
                    speed)
                sock.send(cmd.encode('utf-8'))
                screen.addstr(0, 0, cmd)
            # k = getch.getch()
            # if k=='\x1b':
            #     print('up')
            # elif k=='\x1b[B':
            #     print('down')
            # elif k=='\x1b[C':
            #     print('right')
            # elif k=='\x1b[D':
            #     print('left')
            # else:
            # sock.send("FL50".encode('utf-8'))
            # time.sleep(1)
            # sock.send("BS100".encode('utf-8'))
            # time.sleep(1)
    except KeyboardInterrupt:
        print('[I] User requested exit')
    finally:
        sock.close()
        curses.nocbreak()
        screen.keypad(0)
        curses.echo()
        curses.endwin()
