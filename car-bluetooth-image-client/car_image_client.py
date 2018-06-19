#!/usr/bin/env python

import argparse
import socket
import io
from PIL import Image
import cv2
import numpy as np

# TODO move to utilities
def pil2opencv(pil_image):
    np_array = np.array(pil_image)
    if len(np_array.shape) == 3 and np_array.shape[2] == 3:
        # Convert RGB to BGR
        return np_array[:, :, ::-1] #TODO do we need to copy it? .copy()
    else:
        return np_array


class BluetoothCarImageSubscriber:
    def __init__(self, srv_mac, srv_port, verbose=False):
        self.srv_mac = srv_mac
        self.srv_port = srv_port
        self.verbose = verbose

    def receive_images_forever(self):
        print('[I] Connecting to "{:s}":{:d}'.format(self.srv_mac, self.srv_port))
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((self.srv_mac, self.srv_port))

        try:
            img = self.__receive_image(sock)
            while img is not None:
                mat = pil2opencv(img)
                cv2.imshow('Stream ' + self.srv_mac, mat)
                cv2.waitKey(50)
                #PIL: img.show()
                img = self.__receive_image(sock)
        except KeyboardInterrupt:
            print('[I] User requested exit')
        finally:
            sock.close()


    def __receive_image(self, sock):
        try:
            # Server sends size of image stream (encoded in-memory storage), so make a single read
            data = sock.recv(1024)
            if data and data.decode('utf-8').startswith('size:'):
                # Decode buffer size.
                sz = int(data[5:])
                if self.verbose:
                    print('[I] Receiving image with {} bytes'.format(sz))

                # Read buffer into memory.
                buf = io.BytesIO()
                data = sock.recv(sz)
                while sz > 0:
                    num_rcv = buf.write(data)
                    if self.verbose:
                      print('    Appending {} bytes to buffer'.format(num_rcv))
                    sz = sz - num_rcv
                    data = sock.recv(sz)
                # Decode image from memory.
                image = Image.open(buf)
                return image
            else:
                return None
        except ConnectionResetError:
            print('[W] Server terminated connection')
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac', action='store', help="MAC of the server's bluetooth adapter")
    parser.add_argument('--port', action='store', type=int, help='Port the server is listening on')
    parser.add_argument('--verbose', action='store_true', help='Print debug output while receiving images')
    args = parser.parse_args()
    if args.mac is None:
        print('[WARNING] Using default MAC')
        args.mac = 'B8:27:EB:9B:1B:EA'

    if args.port is None:
        print('[WARNING] Using default port')
        args.port = 3

    client = BluetoothCarImageSubscriber(args.mac, args.port, verbose=args.verbose)
    client.receive_images_forever()
