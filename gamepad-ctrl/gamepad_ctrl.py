#!/usr/bin/env python

import sys

# Zeth's inputs library
sys.path.append('../third_party/inputs')
from inputs import devices, get_gamepad, get_key, get_mouse

def main():
    while True:
        #events = get_key()
        events = get_mouse()
        for event in events:
            print(event.ev_type, event.code, event.state)
  
if __name__ == "__main__":
    main()
