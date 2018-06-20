#!/usr/bin/env python
import socket
from threading import Thread, Lock
from PIL import Image
from io import BytesIO
import time
import pkgutil
import queue


class ThreadSafeDict(dict) :
    def __init__(self, * p_arg, ** n_arg) :
        dict.__init__(self, * p_arg, ** n_arg)
        self._lock = Lock()

    def __enter__(self) :
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback) :
        self._lock.release()
#TODO implement threadsafe image queue which keeps the most up to date image

CQ = ThreadSafeDict()

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
        self.client_queues = ThreadSafeDict()
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
        global CQ
        with CQ as Q:
#with self.client_queues as Q:
            Q[id] = 'foo' #queue.Queue(maxsize=5)
            print('added to Q {}'.format(id))
            print('Size is now {}'.format(len(Q)))
            print(CQ)

    def put_image(self, image):
        global CQ
        print('  +{}'.format(len(CQ)))
        print(CQ)
        print('   {}'.format(len(self.client_queues)))
        time.sleep(0.1)
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
                self.grabber.register_consumer(id)
                print(self.grabber.client_queues)
                thread.start()
        except KeyboardInterrupt:
            print('[I] Exit requested by user within ImagePublishingServer')
        finally:
            self.srv_socket.close() # TODO what happens if we close() a socket twice (see self.terminate)?
