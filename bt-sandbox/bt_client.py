#!/usr/bin/env python

# http://blog.kevindoran.co/bluetooth-programming-with-python-3/
import argparse
import socket
import io
from PIL import Image

def receive_image(sock):
    # Server sends size of image stream (encoded in-memory storage), so make a single read
    data = sock.recv(1024)
    if data and data.decode('utf-8').startswith('size:'):
        # Decode buffer size.
        sz = int(data[5:])
        print(' Server is going to send {} bytes'.format(sz))

        # Read buffer into memory.
        buf = io.BytesIO()
        data = sock.recv(sz)
        while sz > 0:
            num_rcv = buf.write(data)
            #print('append {} bytes to buffer'.format(num_rcv))
            sz = sz - num_rcv
            data = sock.recv(sz)
        print('Received image ({} bytes)'.format(buf.getbuffer().nbytes))
        # Decode image from memory.
        image = Image.open(buf)
        # image.show()
        return image
    else:
        return None

def receive_images_forever(mac, port):
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    print('Trying to connect to "{:s}":{:d}'.format(mac, port))
    sock.connect((mac, port))

    try:
        img = receive_image(sock)
        while img is not None:
            img.show()
            img = receive_image(sock)
    #except Exception as ex:
    #    print('Exception occured')
    #    print(ex)
    finally:
    #while 1:
    #    text = input()
    #    if text == "quit":
    #        break
    #    s.send(bytes(text, 'UTF-8'))
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac', action='store', help="MAC of the server's bluetooth adapter")
    parser.add_argument('--port', action='store', type=int, help='Port the server is listening on')
    args = parser.parse_args()
    if args.mac is None:
        print('[WARNING] Using default MAC')
        args.mac = 'B8:27:EB:9B:1B:EA'

    if args.port is None:
        print('[WARNING] Using default port')
        args.port = 23
    print(args.mac)
    print(args.port, type(args.port))

    receive_images_forever(args.mac, args.port)
