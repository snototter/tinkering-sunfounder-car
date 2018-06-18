#!/usr/bin/env python
# TODO sudo hciconfig hci0 piscan
# otherwise, client won't find the pi!
"""
A simple Python script to receive messages from a client over
Bluetooth using PyBluez (with Python 2).
"""

import bluetooth
from PIL import Image
from io import BytesIO
  
def get_dummy_image_buffer():
    img = Image.open('../car-ctrl-gamepad/figures/gamepad-schematic.png')
    #img.show()
  
    img_memory_file = BytesIO()
    img.save(img_memory_file, "png")
    return img_memory_file  
#client_connection.sendall(fd.getvalue())


#hostMACAddress = '4C:34:88:E1:EB:54' # The MAC address of a Bluetooth adapter on the server. The server might have multiple Bluetooth adapters.
hostMACAddress = 'B8:27:EB:9B:1B:EA'
port = 3
backlog = 1
#size = 1024
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
s.bind((hostMACAddress, port))
s.listen(backlog)
try:
    img_memory_file = get_dummy_image_buffer()
    print('waiting')
    client, clientInfo = s.accept()
    print('connected')
    #while 1:
    #    data = client.recv(size)
    #    if data:
    #        print(data)
    #        client.send(data) # Echo back to client
    #client.sendall(img_memory_file.getvalue())
    client.send('size:' + str(img_memory_file.getbuffer().nbytes))
#fd.getbuffer().nbytes
#42680
except:	
    pass
finally:
    print("Closing socket")
    client.close()
    s.close()
    print("Clean up in-memory image file")
    img_memory_file.close()

