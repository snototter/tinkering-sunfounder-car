#!/usr/bin/env python

import argparse
import socket
import io
# from PIL import Image
# import cv2
# import numpy as np
import threading
import time



if __name__ == "__main__":

    # parser = argparse.ArgumentParser()
    # parser.add_argument('--mac', action='store', help="MAC of the server's bluetooth adapter")
    # parser.add_argument('--port', action='store', type=int, help='Port the server is listening on')
    # parser.add_argument('--verbose', action='store_true', help='Print debug output while receiving images')
    # args = parser.parse_args()
    # if args.mac is None:
    #     print('[WARNING] Using default MAC')
    #     args.mac = 'B8:27:EB:9B:1B:EA'

    # if args.port is None:
    #     print('[WARNING] Using default port')
    #     args.port = 3

    # srv = CarControlTcpServer(args.mac, args.port)
    # srv.serve_clients()
    srv = '127.0.0.1'
    port = 8080
    print('[I] Connecting to "{:s}":{:d}'.format(srv, port))
#         sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((srv, port))

    try:
        while True:
            sock.send("FL50".encode('utf-8'))
            time.sleep(1)
            sock.send("BS100".encode('utf-8'))
            time.sleep(1)
    except KeyboardInterrupt:
        print('[I] User requested exit')
    finally:
        sock.close()
