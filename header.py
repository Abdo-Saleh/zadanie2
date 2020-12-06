import sys
from ctypes import sizeof
import time
from pynput.keyboard import Key, Listener


class Header:
    def __init__(self, state, typ, seq, number_of_fragments, fragment_size, crc):
        # 1 byte, 0- invalid, 2- syn , 4- ack, 8- fin, 16- close
        self.state = state
        # 1 bytes, 1- text, 2- txt, 3- pdf
        self.typ = typ
        # 2 bytes
        self.seq = seq
        # 2 bytes
        self.number_of_fragments = number_of_fragments
        # 2 bytes
        self.fragment_size = fragment_size
        # 2 bytes
        self.crc = crc


import sched, time
s = sched.scheduler(time.time, time.sleep)
def do_something(sc):
    print("Doing stuff...")
    # do your stuff
    s.enter(2, 1, do_something, (sc,))

s.enter(2, 1, do_something, (1,))
s.run()

if True:
    s.cancel()


# start = time.time()
#
#
# def on_press(key):
#     print('{0} pressed'.format(
#         key))
#
#
# def on_release(key):
#     if int(time.time() - start) >= 1:
#         print("detected")
#     print('{0} release'.format(
#         key))
#     if key == Key.esc:
#         # Stop listener
#         return False
#
#
# with Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     listener.join()
