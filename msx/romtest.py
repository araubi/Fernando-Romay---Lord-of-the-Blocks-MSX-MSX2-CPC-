"""Arranque de la ROM en el emulador: cartucho ASCII16 en el slot 1."""
import os
from msx import *
class CartMSX(MSX):
    def __init__(s, rom, seed=1):
        super().__init__(seed); s.rom = rom; s.bank = [0, 0, 0, 0]
    def rd(s, a):
        a &= 0xFFFF; sl = (s.ppi_a >> ((a >> 14) * 2)) & 3
        if sl == 1 and 0x4000 <= a < 0xC000:
            p = a >> 14; return s.rom[(s.bank[p] * 0x4000 + (a & 0x3FFF)) % len(s.rom)]
        return MSX.rd(s, a)
    def wr(s, a, v):
        a &= 0xFFFF; sl = (s.ppi_a >> ((a >> 14) * 2)) & 3
        if sl == 1 and 0x4000 <= a < 0xC000:
            if 0x6000 <= a < 0x6800: s.bank[1] = v & 3
            elif 0x7000 <= a < 0x7800: s.bank[2] = v & 3
            return
        MSX.wr(s, a, v)
def boot(rom, seed=1):
    m = CartMSX(rom, seed); c = Z80(m); install_bios(c)
    # CHGMOD 2 (como SCREEN 2 de BASIC)
    def chgmod(cpu):
        v = m.vdp; v.reg = [0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x11]
        for i in range(768): v.vram[0x1800 + i] = i & 255
        v.vram[0x1B00] = 0xD0
        cpu.PC = cpu.pop(); return True
    c.hooks[0x5F] = chgmod
    m.ram[0xFEE4] = 0xC9; m.ram[0xFD9F] = 0xC9; m.ram[0xFD9A] = 0xC9
    m.ram[0xFCC1:0xFCC9] = b'\0' * 8                 # sin slots expandidos
    m.ppi_a = 0b11110100                              # p0 BIOS, p1 cartucho, p2-3 RAM(3)... p2 se fija en el arranque
    m.ppi_a = (3 << 6) | (0 << 4) | (1 << 2) | 0      # p2 = slot 0 al principio (como si no hubiera RAM ahi)
    c.SP = 0xF380; c.im = 1; c.iff = 0
    init = rom[2] | rom[3] << 8
    c.push(0x0000); c.PC = init
    return m, c
