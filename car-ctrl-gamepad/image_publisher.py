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

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    # Taken from https://stackoverflow.com/a/34177358
    from shutil import which
    return which(name) is not None

def pil2opencv(pil_image):
    np_array = np.array(pil_image)
    if len(np_array.shape) == 3 and np_array.shape[2] == 3:
        # Convert RGB to BGR
        return np_array[:, :, ::-1] #TODO do we need to copy it? .copy()
    else:
        return np_array

# def get_dummy_image_buffer():
#     """Returns an in-memory image file to be sent via the socket"""
#     img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
#     #img.show()
#     img_memory_file = BytesIO()
#     img.save(img_memory_file, "png")
#     return img_memory_file

def numpy2memory_file(np_data, rotate=False):
    """Convert numpy (image) array to ByteIO stream"""
    # print('converting {}'.format(np_data.shape))
    # Rotate 90 deg clockwise (that's what we needed for pygame captures)
    # TODO handle grayvalue (call standard data.transpose)
    if rotate:
        np_data = np.flip(np.transpose(np_data, (1,0,2)), axis=1) # TODO check if also required for cv2
    img = Image.fromarray(np_data)
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file


class ImageGrabber:
    def __init__(self):
        self.keep_alive = True
        self.thread = None
        self.client_queues = {}
        # Check if fswebcam is installed, otherwise fall back to cv2 or pygame
        if is_tool('fswebcam'):
            print('[I] ImageGrabber using fswebcam')
            self.grab_fx = self.__grab_fswebcam
        else:
            cv2_spec = pkgutil.find_loader('cv2')
            if cv2_spec is not None:
                # We have OpenCV, let's use it
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
        self.thread = Thread(target=self.grab_fx)
        self.thread.start()

    def terminate(self):
        self.keep_alive = False
        if self.thread is not None:
            self.thread.join()

    def register_consumer(self, id):
        #self.client_queues.update({id: 'bar'})
        self.client_queues[id] = queue.Queue(maxsize=1)
        print('Registered {}: now has {} items'.format(id, len(self.client_queues)))

    def unsubscribe(self, id):
        self.client_queues.pop(id) # will raise KeyError when called with invalid (unknown) key

    def put_image(self, image_memory_file):
        # mem = np2memory_file(image)
        #print('Processing {} items'.format(len(self.client_queues)))
        for id in self.client_queues.keys():
            q = self.client_queues[id]
            if not q.full():
                q.put(image_memory_file)
                print('  => Putting into q {} [{}]'.format(id, q.qsize()))
            else:
                print('  !! Skipping full q {}'.format(id))

    def get_image_memory_file(self, id):
        if id in self.client_queues:
            img_mem = self.client_queues[id].get(block=True)
            return img_mem
        return None

    def __grab_fswebcam(self):
        import subprocess
        while self.keep_alive:
            # Invoke fswebcam in the shell - this grabs the most recent image
            # and outputs a bytestream onto stdout/into our pipe.
            PIPE = subprocess.PIPE
            proc = subprocess.Popen("fswebcam --no-banner -d /dev/video0 -r 640x480 -q -", shell=True, stderr=PIPE, stdout=PIPE)
            (data, err) = proc.communicate()
            # TODO check error!
            #print(err) => b''
            # Convert the byte buffer into a BytesIO stream which can be sent
            # via our socket.
            self.put_image(BytesIO(data))

    def __grab_cv2(self):
        """Uses OpenCV VideoCapture to grab webcam images - lags a lot"""
        import cv2
        cam = cv2.VideoCapture(0)
        while self.keep_alive:
            success, img = cam.read()
            if success:
                #cv2.imshow("cam-test",img)
                #cv2.waitKey(20)
                np_data = np.asarray(img[:,:,::-1]) # TODO check if this correctly flips the channels, when decoding the bytestream at the bluetooth client
                self.put_image(numpy2memory_file(np_data, rotate=False))

    def __grab_pygame(self):
        """Uses pygame.camera to grab webcam images - lags a lot"""
        import pygame
        import pygame.camera
        import pygame.surfarray

        pygame.camera.init()
        cam_list = pygame.camera.list_cameras()
        if len(cam_list) > 0:
            cam = pygame.camera.Camera(cam_list[0])
            cam.start()
            while self.keep_alive:
                img = cam.get_image()
                if img is not None: #https://stackoverflow.com/a/34674275
                    np_data = pygame.surfarray.array3d(img)
                    self.put_image(numpy2memory_file(np_data, rotate=True))
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
                # Grab image
                img_memory_file = self.grabber.get_image_memory_file(id)
                #img_memory_file = get_dummy_image_buffer()
                # Send image
                if img_memory_file is not None:
                    #print('Going to send {} bytes'.format(img_memory_file.getbuffer().nbytes))
                    header = 'size:{:010d}'.format(img_memory_file.getbuffer().nbytes)
                    client.sendall(bytes(header, 'utf-8'))
                    #client.send(bytes('size:' + str(img_memory_file.getbuffer().nbytes), 'utf-8'))
                    client.sendall(img_memory_file.getvalue())
                # Wait a bit to prevent spamming while debugging/showcasing
                #time.sleep(2)
        except ConnectionResetError:
            print('[I] RFCOMM Client {} disconnected'.format(info))
        finally:
            client.close()
            self.grabber.unsubscribe(id)

    def accept_image_clients(self):
        """Wait for incoming clients, start new serving thread for each."""
        try:
            print('[I] Publisher accepting clients at {} on port {}'.format(self.mac, self.port))
            self.srv_socket.settimeout(0.5)
            while self.keep_alive:
                # Wait for client connection
                try:
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
                except socket.timeout:
                    pass
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
    try:
        quit_event.wait()
    except KeyboardInterrupt:
        print('[I] Exit requested by user within image_publisher.run')
    finally:
        print('[I] Signaling image publishing service to shut down')
        img_server.terminate()
        img_server_thread.join()
