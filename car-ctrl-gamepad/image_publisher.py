#!/usr/bin/env python
import socket
from threading import Thread, Lock
from PIL import Image
from io import BytesIO
import time
import pkgutil
import queue


#TODO implement threadsafe image queue which keeps the most up to date image

def get_dummy_image_buffer():
    """Returns an in-memory image file to be sent via the socket"""
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

class ImageGrabber:
    def __init__(self):
        self.keep_alive = True
        self.thread = None
        self.client_queues = {}
        cv2_spec = pkgutil.find_loader('cv2')
        if cv2_spec is not None:
            # We have OpenCv, let's use it
            print('[I] ImageGrabber using OpenCV')
            self.grab_fx = self.__grab_cv2
        else:
            # Fallback to pygame (should be installed on raspbian by default)
            pyg_spec = pkgutil.find_loader('pygame')
            if pyg_spec is not None:
                print('[I] ImageGrabber using pygame')
                self.grab_fx = self.__grab_pygame
            else:
                raise ModuleNotFoundError('Neither OpenCV nor pygame is available')

    def start(self):
        # Start grabbing in a separate thread
        self.thread = Thread(target = self.grab_fx)
        self.thread.start()

    def terminate(self):
        self.keep_alive = False
        if self.thread is not None:
            self.thread.join()

    def register_consumer(self, id):
        self.client_queues[id] = queue.Queue(maxsize=5)

    def put_image(self, image):
        for id in self.client_queues.keys():
            q = self.client_queues[id]
            if not q.full():
                q.put(image)
                print('Putting: {}'.format(image))

    def __grab_cv2(self):
        import cv2
        cam = cv2.VideoCapture(0)
        while self.keep_alive:
            success, img = cam.read()
            if success:
                cv2.imshow("cam-test",img)
                cv2.waitKey(20)
                self.put_image('foo')
                #TODO add to queue for client
            #imwrite("filename.jpg",img)

    def __grab_pygame(self):
        #TODO implement and check!
        import pygame
        import pygame.camera

        pygame.camera.init()
        pygame.camera.list_camera() #Camera detected or not
        cam = pygame.camera.Camera("/dev/video0",(640,480))
        cam.start()
        img = cam.get_image()
        pygame.image.save(img,"filename.jpg")



class ImagePublishingServer:
    def __init__(self, mac, port=42, backlog=5):
        self.mac = mac
        self.port = port
        self.backlog = backlog

        self.client_handler = {}

        self.srv_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind((self.mac, self.port))
        self.srv_socket.listen(self.backlog)
        self.keep_alive = True

        self.client_thread_lock = Lock()
        self.client_thread_count = 0

        self.grabber = ImageGrabber()
        self.grabber.start()

    def get_client_id(self):
        with self.client_thread_lock:
            id = self.client_thread_count
            self.client_thread_count += 1
        return id

    def run(self):
        """Blocking call to wait (and deal with) incoming clients"""
        # TODO set up image collector in separate thread, which pushed into per-client queues
        self.accept_image_clients()

    def terminate(self):
        print('[I] Shutting down image publisher')
        self.keep_alive = False

        # Wait for connected handler to close connections
        for id in self.client_handler.keys():
            thread, client = self.client_handler[id]
            client.close()
            thread.join()
            self.client_handler[id] = None

        # Close socket
        self.srv_socket.close()

        self.grabber.terminate()

    def handle_client(self, id, client, info):
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
            print('[I] RFCOMM Client {} disconnected'.format(info))
        finally:
            client.close()

    def accept_image_clients(self):
        """Wait for incoming clients, start new serving thread for each."""
        client = None
        try:
            #img_memory_file = get_dummy_image_buffer()
            while self.keep_alive:
                print('[I] Publisher accepting clients at {} on port {}'.format(self.mac, self.port))
                client, info = self.srv_socket.accept()
                print('[I] RFCOMM client {} connected'.format(info))
                id = self.get_client_id()
                thread = Thread(target = self.handle_client, args=(id, client, info,))
                #self.client_handler.append(thread)
                self.client_handler[id] = (thread, client)
                thread.start()
        except KeyboardInterrupt:
            print('[I] Exit requested by user within ImagePublishingServer')
        finally:
            self.srv_socket.close() # TODO what happens if we close() a socket twice (see self.terminate)?
