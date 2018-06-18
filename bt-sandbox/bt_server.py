#!/usr/bin/env python
# TODO sudo hciconfig hci0 piscan
# otherwise, client won't find the pi!

import argparse
import bluetooth
from PIL import Image
from io import BytesIO
import time

def get_dummy_image_buffer():
    """Returns an in-memory image file to be sent via the socket"""
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

def serve_image_listeners_forever(server_address, backlog)
    """Set up socket and send images to connected clients."""
    # mac = server_address[0]
    # port = server_address[1]
    srv_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    srv_socket.bind(server_address)
    srv_socket.listen(backlog)
    try:
        img_memory_file = get_dummy_image_buffer()

        print('Waiting for client connection')
        client, info = srv_socket.accept()
        print('Connected to {}'.format(info))
        # TODO make separate thread to handle request
        for i in range(3):
            client.send('size:' + str(img_memory_file.getbuffer().nbytes))
            client.sendall(img_memory_file.getvalue())
            time.sleep(5) # wait 5sec

    # except:
    #     #TODO log
    #     pass
    finally:
        print("Closing socket")
        client.close()
        srv_socket.close()
        print("Clean up in-memory image file")
        img_memory_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac', action='store', help='MAC of the bluetooth adapter')
    parser.add_argument('--port', action='store', help='Port to be listening on')
    parser.add_argument('--max-connections', action='store', help='Max. number of allowed client connections')
    args = parser.parse_args()
    if args.mac is None:
        print('[WARNING] Using default MAC')
        args.mac = 'B8:27:EB:9B:1B:EA'

    if args.port is None:
        print('[WARNING] Using default port')
        args.port = 23

    if args.max_connections is None:
        print('[WARNING] Using default max. number of client connections')
        args.max_connections = 3

    serve_image_listeners_forever((args.mac, args.port), args.max_connections)
