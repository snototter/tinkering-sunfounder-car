#!/usr/bin/env python

import threading
import time

class Test:
    def __init__(self):
        self.D = {}
        self.thread = threading.Thread(target=self.run)
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
    t.register(10)
    t.register(23)

    time.sleep(5)

    t.terminate()
