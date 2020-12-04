import sys
from ctypes import sizeof


class Header:
    def __init__(self, typ, index, number_of_fragments, fragment_size, crc):
        # 2 bytes
        self.typ = typ
        # 4 bytes
        self.index = index
        # 4 bytes
        self.number_of_fragments = number_of_fragments
        # 4 bytes
        self.fragment_size = fragment_size
        # 2 bytes
        self.crc = crc



