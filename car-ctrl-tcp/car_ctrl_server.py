#!/usr/bin/env python

import argparse
import socket
import io
# from PIL import Image
# import cv2
# import numpy as np
import threading
import time


class CarControlTcpServer:
    # To be run on Pi
    def __init__(self, mac, port=42, backlog=1):
        #mac for bluetooth, ip otherwise
        self.mac = mac
        self.port = port
        self.backlog = backlog

        self.client_handler = {}

        if True:
            self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.mac = '127.0.0.1'
            self.port = 8080
        else:
            # self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.srv_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind((self.mac, self.port))
        self.srv_socket.listen(self.backlog)
        self.keep_alive = True

        self.client_thread_lock = threading.Lock()
        self.client_thread_count = 0


    def get_client_id(self):
        with self.client_thread_lock:
            id = self.client_thread_count
            self.client_thread_count += 1
        return id

    def run(self):
        """Blocking call to wait (and deal with) incoming clients"""
        self.serve_clients()

    def terminate(self):
        print('[I] Shutting down car controller')
        self.keep_alive = False

        # Wait for connected handler to close connections
        for id in self.client_handler.keys():
            thread, client = self.client_handler[id]
            client.close()
            thread.join()
            self.client_handler[id] = None

        # Close socket
        self.srv_socket.close()

    def handle_client(self, id, client, info):
        try:
            while self.keep_alive:
                data = client.recv(4096)
                if not data:
                    break
                datastr = data.decode('utf-8').lower()
                print('Client sent me: ', datastr)
                is_forward = datastr[0] == 'f'
                turn_left = datastr[1] == 'l'
                straight = datastr[1] == 's'
                speed = int(datastr[2:])
                print(is_forward, turn_left, speed)


            self.keep_alive = False

                # # Grab image
                # img_memory_file = self.grabber.get_image_memory_file(id)
                # #img_memory_file = get_dummy_image_buffer()
                # # Send image
                # if img_memory_file is not None:
                #     #print('Going to send {} bytes'.format(img_memory_file.getbuffer().nbytes))
                #     header = 'size:{:010d}'.format(img_memory_file.getbuffer().nbytes)
                #     client.sendall(bytes(header, 'utf-8'))
                #     #client.send(bytes('size:' + str(img_memory_file.getbuffer().nbytes), 'utf-8'))
                #     client.sendall(img_memory_file.getvalue())
                # # Wait a bit to prevent spamming while debugging/showcasing
                # #time.sleep(2)
        except ConnectionResetError:
            print('[I] Client {} disconnected'.format(info))
        finally:
            client.close()

    def serve_clients(self):
        """Wait for incoming client."""
        try:
            print('[I] Accepting clients at {} on port {}'.format(self.mac, self.port))
            self.srv_socket.settimeout(0.5)
            while self.keep_alive:
                # Wait for client connection
                try:
                    client, info = self.srv_socket.accept()
                    print('[I] RFCOMM client {} connected'.format(info))
                    #time.sleep(1)
                    # Register with image grabber and start handling thread
                    id = self.get_client_id()
                    thread = threading.Thread(target = self.handle_client, args=(id, client, info,))
                    #self.client_handler.append(thread)
                    self.client_handler[id] = (thread, client)
                    thread.start()
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print('[I] Exit requested by user')
            self.terminate()
        finally:
            self.srv_socket.close() # TODO what happens if we close() a socket twice (see self.terminate)?

# def run(quit_event, mac, port, backlog):
#     # Start up server
#     img_server = ImagePublishingServer(mac, port, backlog=backlog)
#     img_server_thread = Thread(target=img_server.run)
#     img_server_thread.start()
#
#     # Wait for termination signal
#     try:
#         quit_event.wait()
#     except KeyboardInterrupt:
#         print('[I] Exit requested by user within image_publisher.run')
#     finally:
#         print('[I] Signaling image publishing service to shut down')
#         img_server.terminate()
#         img_server_thread.join()

# # TODO move to utilities
# def pil2opencv(pil_image):
#     np_array = np.array(pil_image)
#     if len(np_array.shape) == 3 and np_array.shape[2] == 3:
#         # Convert RGB to BGR
#         return np_array[:, :, ::-1] #TODO do we need to copy it? .copy()
#     else:
#         return np_array


# class BluetoothCarImageSubscriber:
#     def __init__(self, srv_mac, srv_port, verbose=False):
#         self.srv_mac = srv_mac
#         self.srv_port = srv_port
#         self.verbose = verbose

#     def receive_images_forever(self):
#         print('[I] Connecting to "{:s}":{:d}'.format(self.srv_mac, self.srv_port))
#         sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
#         sock.connect((self.srv_mac, self.srv_port))

#         try:
#             img = self.__receive_image(sock)
#             while img is not None:
#                 mat = pil2opencv(img)
#                 cv2.imshow('Stream ' + self.srv_mac, mat)
#                 cv2.waitKey(50)
#                 #PIL: img.show()
#                 img = self.__receive_image(sock)
#         except KeyboardInterrupt:
#             print('[I] User requested exit')
#         finally:
#             sock.close()


#     def __receive_image(self, sock):
#         try:
#             # Server sends size of image stream (encoded in-memory storage), so make a single read
#             st1 = time.time()
#             data = sock.recv(15)
#             # TODO ensure that we really received 15 bytes, not less!
#             if data is not None and data.decode('utf-8').startswith('size:'):
#                 # Decode buffer size.
#                 sz = int(data[5:])
#                 if self.verbose:
#                     print('[I] Receiving image with {} bytes'.format(sz))

#                 st2 = time.time()
#                 # Read buffer into memory.
#                 buf = io.BytesIO()
#                 data = sock.recv(sz)
#                 while sz > 0:
#                     num_rcv = buf.write(data)
#                     if self.verbose:
#                       print('    Appending {} bytes to buffer'.format(num_rcv))
#                     sz = sz - num_rcv
#                     data = sock.recv(sz)
#                 if self.verbose:
#                     print('    Trying to decode {} bytes'.format(buf.getbuffer().nbytes))
#                 st3 = time.time()
#                 # Decode image from memory.
#                 image = Image.open(buf)
#                 st4 = time.time()
#                 print('[I] Waited {} s for response, {} s to receive, {} s to decode'.format(st2-st1, st3-st2, st4-st3))
#                 return image
#             else:
#                 return None
#         except ConnectionResetError:
#             print('[W] Server terminated connection')
#         return None


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

    srv = CarControlTcpServer(args.mac, args.port)
    srv.serve_clients()
