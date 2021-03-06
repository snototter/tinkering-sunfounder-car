#!/bin/bash --

# Although we should be initialized after bluetooth is up, we experienced issues (so let's wait a bit longer, and see if that fixes the bluetooth connection problems)
sleep 10
# Make device discoverable by the bluetooth peers
sudo hciconfig hci0 piscan

# Get mac address of first bluetooth adapter - watch out if you have multiple!
btmac=$(hcitool dev | grep -o -m 1 "[[:xdigit:]:]\{11,17\}")

# Start up server
source .venv/bin/activate
python gamepad_ctrl.py --bt-img-srv-mac=${btmac} --bt-img-srv-port=3 --runon=pi


