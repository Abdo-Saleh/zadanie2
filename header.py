import sys
from ctypes import sizeof
import time


class Header:
    def __init__(self, state, typ, seq, number_of_fragments, fragment_size, crc):
        # 1 byte, 0- invalid, 2- syn (init), 4- ack, 8- fin, 16- close
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
