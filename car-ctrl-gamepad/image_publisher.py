#!/usr/bin/env python
import socket
from threading import Thread
from PIL import Image
from io import BytesIO
import time

#TODO implement threadsafe image queue which keeps the most up to date image

def get_dummy_image_buffer():
    """Returns an in-memory image file to be sent via the socket"""
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

class ImagePublishingServer:
    def __init__(self, mac, port=42, backlog=5):
        self.mac = mac
        self.port = port
        self.backlog = backlog

        self.srv_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind((self.mac, self.port))
        self.srv_socket.listen(self.backlog)
        self.keep_alive = True

        self.client_handler = []
        # Start new thread
        #self.thread = Thread(target = self.accept_image_clients)
        #self.thread.start()

    def run(self):
        # TODO set up image queue in separate thread
        self.accept_image_clients()

    def terminate(self):
        print('[I] Shutting down image publisher')
        self.keep_alive = False

        # Wait for connected handler to close connections
        for t in self.client_handler:
            t.join()

        # Close socket
        self.srv_socket.close()

    def handle_client(self, client, info):
        try:
            while self.keep_alive:
                # Grab image TODO
                img_memory_file = get_dummy_image_buffer()
                # Send image
                if img_memory_file is not None:
                    client.send(bytes('size:' + str(img_memory_file.getbuffer().nbytes), 'utf-8'))
                    client.sendall(img_memory_file.getvalue())
                # Wait a bit to prevent spamming while debugging/showcasing
                time.sleep(2)
        except ConnectionResetError:
            print('[I] Client {} disconnected'.format(info))
        finally:
            client.close()

    def accept_image_clients(self):
        """Wait for incoming clients, start new serving thread for each."""
        client = None
        try:
            #img_memory_file = get_dummy_image_buffer()
            while self.keep_alive:
                print('[I] Waiting for client connection\nMAC {} on port {}'.format(self.mac, self.port))
                client, info = self.srv_socket.accept()
                print('[I] Connected to {}'.format(info))
                thread = Thread(target = self.handle_client, args=(client, info,))
                self.client_handler.append(thread)
                thread.start()
        except KeyboardInterrupt:
            pass
        finally:
            pass
