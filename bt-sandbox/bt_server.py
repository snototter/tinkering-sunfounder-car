#!/usr/bin/env python

import argparse
#import bluetooth
import socket
from PIL import Image
from io import BytesIO
import time

#TODO 1 sending thread per client https://stackoverflow.com/questions/2905965/creating-threads-in-python
#TODO capture image from webcam, notify threads
#TODO keep list of threads to join upon cleanup
def get_dummy_image_buffer():
    """Returns an in-memory image file to be sent via the socket"""
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

def serve_image_listeners_forever(server_address, backlog):
    """Set up socket and send images to connected clients."""
    # mac = server_address[0]
    # port = server_address[1]
#pybluez:
#    srv_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
#    srv_socket.bind(server_address)
#    srv_socket.listen(backlog)
    srv_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    srv_socket.bind(server_address)
    srv_socket.listen(backlog)
    client = None
    try:
        img_memory_file = get_dummy_image_buffer()

        print('Waiting for client connection\nMAC {} on port {}'.format(server_address[0], server_address[1]))
        client, info = srv_socket.accept()
        print('Connected to {}'.format(info))
        # TODO make separate thread to handle request
        for i in range(3):
            client.send(bytes('size:' + str(img_memory_file.getbuffer().nbytes), 'utf-8'))
            client.sendall(img_memory_file.getvalue())
            time.sleep(5) # wait 5sec
    except Exception as ex:
        #TODO log
        print('Exception occured')
        print(ex)
    finally:
        print("Closing sockets")
        if client is not None:
            client.close()
        srv_socket.close()
        print("Clean up in-memory image file")
        img_memory_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac', action='store', help='MAC of the bluetooth adapter')
    parser.add_argument('--port', action='store', type=int, help='Port to be listening on')
    parser.add_argument('--max-connections', action='store', type=int, help='Max. number of allowed client connections')
    args = parser.parse_args()
    if args.mac is None:
        print('[WARNING] Using default MAC')
        args.mac = 'B8:27:EB:9B:1B:EA'

    if args.port is None:
        print('[WARNING] Using default port')
        args.port = 3

    if args.max_connections is None:
        print('[WARNING] Using default max. number of client connections')
        args.max_connections = 5

    serve_image_listeners_forever((args.mac, args.port), args.max_connections)
