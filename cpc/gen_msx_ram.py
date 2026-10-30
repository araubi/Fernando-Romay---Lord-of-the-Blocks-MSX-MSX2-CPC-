"""Genera msx_ram.bin (juego MSX1 ORIGINAL) y msxfin_ram.bin (MSX1 del hack) ejecutando cada cinta en el
emulador MSX de ../msx hasta el menu. De ahi salen los graficos de saltos, tiros y mates que se pasan al CPC
(p_jumps, p_heads). La cinta original no esta en el repositorio.
Uso: python3 gen_msx_ram.py original.cas ../releases/Fernando_Romay_Lord_of_the_Blocks_MSX1.cas"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'msx'))
os.environ.setdefault('MSX_FRAME', '71364')
from msx import load_from_cas
def ram(cas, frames=300):
    m, c = load_from_cas(open(cas, 'rb').read()); m.slot = lambda p: 0
    while c.frames < frames: c.step()
    return bytes(m.ram)
if __name__ == '__main__':
    open(os.path.join(HERE, 'msx_ram.bin'), 'wb').write(ram(sys.argv[1]))
    open(os.path.join(HERE, 'msxfin_ram.bin'), 'wb').write(ram(sys.argv[2]))
