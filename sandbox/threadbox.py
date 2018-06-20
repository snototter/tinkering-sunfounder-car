#!/usr/bin/env python

#import threading
#import time

import socket
from threading import Thread, Lock
from PIL import Image
from io import BytesIO
import time
import pkgutil
import queue
import numpy as np


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
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.grab_fx()

    def terminate(self):
        self.keep_alive = False
        if self.thread is not None:
            self.thread.join()

    def register_consumer(self, id):
        self.client_queues[id] = 'foo' #queue.Queue(maxsize=5)
        print('Registered {}: now has {} items'.format(id, len(self.client_queues)))


    def put_image(self, image):
        print('Processing {} items'.format(len(self.client_queues)))
        time.sleep(0.5)
#        with self.client_queues as Q:
#            print(Q)

#        print('process {} Qs'.format(len(self.client_queues)))
#        for id in self.client_queues.keys():
#            q = self.client_queues[id]
#            if not q.full():
#                q.put(image)
#                print('Putting: {}'.format(image))

    def __grab_cv2(self):
        import cv2
        cam = cv2.VideoCapture(0)
        while self.keep_alive:
            success, img = cam.read()
            if success:
                cv2.imshow("cam-test",img)
                cv2.waitKey(20)
                np_data = np.asarray(img[:,:,::-1]) # check if this correctly flips the channels!
                self.put_image(np_data)
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
            #pygame.image.save(img,"filename.jpg")
        else:
            #TODO raise Error
            pass

class Test:
    def __init__(self):
        self.D = {}
        self.thread = Thread(target=self.run)
        self.keep_alive = True
        self.thread.start()


    def run(self):
        while self.keep_alive:
            time.sleep(1)
            print('RUN: {}'.format(len(self.D)))

    def register(self, k):
        self.D[k] = 'foo';
        print('Registered {}: now has {} items'.format(k, len(self.D)))

    def terminate(self):
        self.keep_alive = False
        print('TERMINATE WITH: {} items'.format(len(self.D)))
        self.thread.join()

if __name__ == "__main__":
    t = Test()
    t.register(1)
    time.sleep(2)
    t.register(10)
    t.register(23)

    time.sleep(1)

    t.terminate()

    g = ImageGrabber()
    g.start()
    time.sleep(1)
    g.register_consumer(23)
    time.sleep(0.5)
    g.register_consumer(15)
    time.sleep(3)
    g.terminate()
