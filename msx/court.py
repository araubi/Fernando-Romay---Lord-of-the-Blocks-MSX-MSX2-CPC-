import numpy as np
from common import files
B0=0xB498
def court_bits(f3):
    a=B0-0x84D0; raw=f3[a:a+0xE00]
    return np.array([[bool(raw[r*32+x//8]&(0x80>>(x%8))) for x in range(256)] for r in range(112)])
def put_bits(f3,bits):
    a=B0-0x84D0
    for r in range(112):
        for bx in range(32):
            v=0
            for k in range(8):
                if bits[r,bx*8+k]: v|=0x80>>k
            f3[a+r*32+bx]=v
