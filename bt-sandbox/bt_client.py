#!/usr/bin/env python

# http://blog.kevindoran.co/bluetooth-programming-with-python-3/
"""
A simple Python script to send messages to a sever over Bluetooth using
Python sockets (with Python 3.3 or above).
"""

import socket
import io
from PIL import Image

#serverMACAddress = '4C:34:88:E1:EB:54'
serverMACAddress = 'B8:27:EB:9B:1B:EA'
port = 3
s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.connect((serverMACAddress,port))

buf_size = 1024
data = s.recv(buf_size)
if data and data.decode('utf-8').startswith('size:'):
    sz = int(data[5:])
    print(' Server is going to send {} bytes'.format(sz))
    buf = io.BytesIO()
    data = s.recv(sz)
    while sz > 0:
    #if data:
        num_rcv = buf.write(data)
        print('append {} bytes to buffer'.format(num_rcv))
        sz = sz - num_rcv
#        print('image received, now decode...')
        #fd = io.BytesIO(data)
        #print(fd.getbuffer().nbytes)
        data = s.recv(sz)
        #image = Image.open(io.BytesIO(data))
        #image.show()
        #image.save(savepath)
    print('Finished loop :-), read {} bytes'.format(buf.getbuffer().nbytes))
    image = Image.open(buf)
    image.show()
else:
    #TODO raise exception
    pass

#while 1:
#    text = input()
#    if text == "quit":
#        break
#    s.send(bytes(text, 'UTF-8'))
s.close()
