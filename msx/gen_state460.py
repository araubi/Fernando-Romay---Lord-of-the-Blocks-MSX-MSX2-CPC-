"""Genera state460.pkl (VRAM y RAM del juego ORIGINAL en el fotograma 460, ya en el partido) a partir de la
cinta original, que no se incluye en el repositorio. Lo usan court_shadow.py y board_patch.py.
Uso: python3 gen_state460.py ruta/al/original.cas"""
import os, sys, pickle
os.environ.setdefault('MSX_FRAME', '71364')
from session import *
from common import CAS
cas = sys.argv[1] if len(sys.argv) > 1 else CAS
m, c = load_from_cas(open(cas, 'rb').read()); m.slot = lambda p: 0
ev = sorted(press('SPACE', 120) + press('1', 340) + press('1', 400))
def onf(cpu):
    while ev and ev[0][0] <= cpu.frames:
        _, k, dn = ev.pop(0); r, b = KEY[k]; m.keys[r] = (m.keys[r] & ~(1 << b)) if dn else (m.keys[r] | (1 << b))
c.on_frame = onf
while c.frames < 460: c.step()
out = sys.argv[2] if len(sys.argv) > 2 else 'state460.pkl'
pickle.dump((bytes(m.vdp.vram), bytes(m.ram)), open(out, 'wb'))
