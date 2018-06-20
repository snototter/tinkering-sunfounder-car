#!/usr/bin/env python
from PIL import Image
import io
import time
#import numpy as np
import os
import subprocess
import threading

class OutputStream(threading.Thread):
    def __init__(self):
        super(OutputStream, self).__init__()
        self.done = False
        self.buffer = BytesIO()
        self.read, self.write = os.pipe()
        self.reader = os.fdopen(self.read, mode='rb')
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
            self.buffer.write(self.reader.read())

        self.reader.close()

    def close(self):
        self.done = True
        os.close(self.write)


if __name__ == "__main__":
    # https://stackoverflow.com/questions/38979075/python-valueerror-embedded-null-byte-when-reading-png-file-from-bash-pipe
    PIPE = subprocess.PIPE
#    p = subprocess.Popen("fswebcam -p YUYV -d /dev/video0 -i 0 -", shell=True, stderr=PIPE, stdout=PIPE)
    p = subprocess.Popen("fswebcam -i 0 -r 640x480 -q -", shell=True, stderr=PIPE, stdout=PIPE)
    (data, err) = p.communicate()
    #print(err) => b''
    #print(err is None)
    pil_image = Image.open(io.BytesIO(data))
    pil_image.show()
    #print(out)
#    self.video.setFrame(out)
#        fswebcam -q
    # with OutputStream() as stream:
    # #while self.keep_alive:
    #     proc = subprocess.Popen(['fswebcam', '-q', '-'], stdout=stream)
    #
    # #proc = subprocess.Popen(['fswebcam', '-q', '-'], stdout=stream)
    #     proc.wait() # could also .poll in a loop
    #     #print('Proc finished?')
    #     print('buffer has {} bytes'.format(stream.buffer.getbuffer().nbytes))
    #     #TODO put_image w/o loading PIL and conversion horror
    #     pil_image = Image.open(stream.buffer)
    #     #pil_image = Image.open('grab.jpg')
    #     #print('Image loaded from disk...')
    #     #np_array = np.array(pil_image)
    #     #self.put_image(np_array)
    #     pil_image.show()
