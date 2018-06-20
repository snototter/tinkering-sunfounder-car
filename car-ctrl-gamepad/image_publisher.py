#!/usr/bin/env python
import socket
from threading import Thread, Lock
from PIL import Image
from io import BytesIO
import time
import pkgutil
import queue
import numpy as np
import multiprocessing

def get_dummy_image_buffer():
    """Returns an in-memory image file to be sent via the socket"""
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

def np2memory_file(np_data):
    print('converting {}'.format(np_data.shape))
    # Rotate 90 deg clockwise (that's what we needed for pygame captures)
    # TODO handle grayvalue (call standard data.transpose)
    np_data = np.flip(np.transpose(np_data, (1,0,2)), axis=1)
    img = Image.fromarray(np_data)
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file

#TODO clean up imports, check exceptions if fswebcam not installed, etc

import os
import subprocess
#import threading
#https://codereview.stackexchange.com/questions/105726/outputstream-class-for-use-with-subprocess-popen
class OutputStream(Thread):
    def __init__(self):
        super(OutputStream, self).__init__()
        self.done = False
        self.buffer = BytesIO()
        self.read, self.write = os.pipe()
        self.reader = os.fdopen(self.read)
        self.start()

    def fileno(self):
        return self.write

    def __enter__(self):
    # Theoretically could be used to set up things not in __init__
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def run(self):
        while not self.done:
            self.buffer.write(self.reader.readline())

        self.reader.close()

    def close(self):
        self.done = True
        os.close(self.write)


class ImageGrabber:
    def __init__(self):
        self.keep_alive = True
        self.thread = None
        self.client_queues = {}
        cv2_spec = pkgutil.find_loader('cv2')
        if False: #TODO temporarily deactivated because of broken dependencies on pi (after pip install), cv2_spec is not None:
            # We have OpenCv, let's use it
            print('[I] ImageGrabber using OpenCV')
            self.grab_fx = self.__grab_cv2
        else:
            # Fallback to pygame (should be installed on raspbian by default)
            pyg_spec = pkgutil.find_loader('pygame')
            if pyg_spec is not None:
                print('[I] ImageGrabber using pygame')
                self.grab_fx = self.__grab_pygame
                self.grab_fx = self.__grab_fswebcam
            else:
                raise ModuleNotFoundError('Neither OpenCV nor pygame is available')

    def start(self):
        # Start grabbing in a separate thread
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.grab_fx()

    def terminate(self):
        self.keep_alive = False
        if self.thread is not None:
            self.thread.join()

    def register_consumer(self, id):
        #self.client_queues.update({id: 'bar'})
        self.client_queues[id] = queue.Queue(maxsize=2)
        print('Registered {}: now has {} items'.format(id, len(self.client_queues)))


    def put_image(self, image):
        mem = np2memory_file(image)
        #print('Processing {} items'.format(len(self.client_queues)))
        for id in self.client_queues.keys():
            q = self.client_queues[id]
            if not q.full():
                q.put(mem)
                print('  => Putting into q {} [{}]'.format(id, q.qsize()))

    def get_image_memory_file(self, id):
        if id in self.client_queues:
            img_mem = self.client_queues[id].get(block=True)
            return img_mem
        return None

    def __grab_fswebcam(self):
#        fswebcam -q
#        with OutputStream() as stream:
        while self.keep_alive:
            proc = subprocess.Popen(['fswebcam', '-q', 'grab.jpg'])
        #proc = subprocess.Popen(['fswebcam', '-q', '-'], stdout=stream)
            proc.wait() # could also .poll in a loop
            #print('Proc finished?')
        #print('buffer has {} bytes'.format(stream.getbuffer().nbytes))
            #TODO put_image w/o loading PIL and conversion horror
            #pil_image = Image.open(stream)
            pil_image = Image.open('grab.jpg')
            #print('Image loaded from disk...')
            np_array = np.array(pil_image)
            self.put_image(np_array)

    def __grab_cv2(self):
        import cv2
        cam = cv2.VideoCapture(0)
        while self.keep_alive:
            success, img = cam.read()
            if success:
                #cv2.imshow("cam-test",img)
                #cv2.waitKey(20)
                np_data = np.asarray(img[:,:,::-1]) # check if this correctly flips the channels!
                self.put_image(np_data)
                #time.sleep(0.5)
                #TODO add to queue for client
            #imwrite("filename.jpg",img)

    def __grab_pygame(self):
        #TODO implement and check!
        import pygame
        import pygame.camera
        import pygame.surfarray

        pygame.camera.init()
        cam_list = pygame.camera.list_cameras()
        if len(cam_list) > 0: #Camera detected or not
            cam = pygame.camera.Camera(cam_list[0])
            cam.start()
            while self.keep_alive:
                img = cam.get_image()
                if img is not None: #https://stackoverflow.com/a/34674275
                    np_data = pygame.surfarray.array3d(img)
                    self.put_image(np_data)
                    #time.sleep(0.5)
            #pygame.image.save(img,"filename.jpg")
        else:
            #TODO raise Error
            pass


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
                img_memory_file = self.grabber.get_image_memory_file(id)
                #img_memory_file = get_dummy_image_buffer()
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
        try:
            while self.keep_alive:
                # Wait for client connection
                print('[I] Publisher accepting clients at {} on port {}'.format(self.mac, self.port))
                client, info = self.srv_socket.accept()
                print('[I] RFCOMM client {} connected'.format(info))
                #time.sleep(1)
                # Register with image grabber and start handling thread
                id = self.get_client_id()
                thread = Thread(target = self.handle_client, args=(id, client, info,))
                #self.client_handler.append(thread)
                self.client_handler[id] = (thread, client)
                self.grabber.register_consumer(id)
                thread.start()
        except KeyboardInterrupt:
            print('[I] Exit requested by user within ImagePublishingServer')
        finally:
            self.srv_socket.close() # TODO what happens if we close() a socket twice (see self.terminate)?

def run(quit_event, mac, port, backlog):
    # Start up server
    img_server = ImagePublishingServer(mac, port, backlog=backlog)
    img_server_thread = Thread(target=img_server.run)
    img_server_thread.start()

    # Wait for termination signal
    quit_event.wait()
    img_server.terminate()
    img_server_thread.join()
