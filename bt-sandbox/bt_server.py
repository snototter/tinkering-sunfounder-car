#!/usr/bin/env python
# TODO sudo hciconfig hci0 piscan
# otherwise, client won't find the pi!
"""
A simple Python script to receive messages from a client over
Bluetooth using PyBluez (with Python 2).
"""

import bluetooth

#hostMACAddress = '4C:34:88:E1:EB:54' # The MAC address of a Bluetooth adapter on the server. The server might have multiple Bluetooth adapters.
hostMACAddress = 'B8:27:EB:9B:1B:EA'
port = 3
backlog = 1
size = 1024
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
s.bind((hostMACAddress, port))
s.listen(backlog)
try:
    print('waiting')
    client, clientInfo = s.accept()
    print('connected')
    while 1:
        data = client.recv(size)
        if data:
            print(data)
            client.send(data) # Echo back to client
except:	
    print("Closing socket")
    client.close()
    s.close()
