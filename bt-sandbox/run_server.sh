#!/bin/bash --

# Make device discoverable by the bluetooth peers
sudo hciconfig hci0 piscan

# Get mac address of first bluetooth adapter - watch out if you have multiple!
btmac=$(hcitool dev | grep -o -m 1 "[[:xdigit:]:]\{11,17\}")

# Start up server
source .venv/bin/activate
python bt_server.py --mac=${btmac} --port=3 --max-connections=5




