"""Extension MSX2 minima del emulador: VDP V9938 en modo G3 (SCREEN 4) con sprites modo 2
(colores por linea, CC/OR, EC, 8 por linea), paleta (R#16 + puerto 9Ah), cartucho ASCII16."""
from msx import *
import romtest

DEFPAL = [(0,0,0),(0,0,0),(1,6,1),(3,7,3),(1,1,7),(2,3,7),(5,1,1),(2,6,7),
          (7,1,1),(7,3,3),(6,6,1),(6,6,4),(1,4,1),(6,2,5),(5,5,5),(7,7,7)]


class VDP2(VDP):
    def __init__(s):
        super().__init__(); s.reg = [0] * 48; s.pal = list(DEFPAL); s.plat = None
        s.vram = bytearray(0x20000); s.hi = 0
    def wctrl(s, v):
        if s.latch is None: s.latch = v; return
        lo = s.latch; s.latch = None
        if v & 0x80:
            r = v & 0x3F
            if r < 48: s.reg[r] = lo
            if r == 16: s.plat = None
        else:
            s.addr = ((v & 0x3F) << 8) | lo; s.hi = s.reg[14] & 7
            if not v & 0x40: s.rbuf = s.vram[s.hi << 14 | s.addr]; s.addr = (s.addr + 1) & 0x3FFF
    def wdata(s, v):
        s.latch = None
        if s.log is not None: s.log(s.addr if not s.hi else (s.hi << 14 | s.addr), v)
        s.vram[s.hi << 14 | s.addr] = v; s.rbuf = v; s.addr = (s.addr + 1) & 0x3FFF
    def rdata(s):
        s.latch = None; v = s.rbuf; s.rbuf = s.vram[s.hi << 14 | s.addr]; s.addr = (s.addr + 1) & 0x3FFF; return v
    def wpal(s, v):
        if s.plat is None: s.plat = v; return
        i = s.reg[16] & 15; rb = s.plat; s.plat = None
        s.pal[i] = ((rb >> 4) & 7, v & 7, rb & 7)
        s.reg[16] = (s.reg[16] + 1) & 15
    def rgb(s, i):
        r, g, b = s.pal[i]; return (r * 255 // 7, g * 255 // 7, b * 255 // 7)
    def render(s, sprites=True):
        r = s.reg; v = s.vram
        P = [s.rgb(i) for i in range(16)]
        im = Image.new('RGB', (256, 192), P[r[7] & 15]); px = im.load()
        nt = (r[2] & 0x0F) << 10; ct = (r[3] & 0x80) << 6; pt = (r[4] & 0x04) << 11
        bd = r[7] & 15
        if not (r[1] & 0x40): return im
        for y in range(192):
            third = y >> 6
            for tx in range(32):
                ch = v[nt + (y >> 3) * 32 + tx] + third * 256
                p = v[pt + ch * 8 + (y & 7)]; c = v[ct + ch * 8 + (y & 7)]
                fg, bg = c >> 4, c & 15
                for k in range(8):
                    col = fg if p & (0x80 >> k) else bg
                    if col == 0: col = bd
                    px[tx * 8 + k, y] = P[col]
        if not sprites: return im
        mode2 = (r[0] & 0x0E) == 0x04
        if not mode2:
            return im
        sat = ((r[11] & 3) << 15) | ((r[5] & 0xFC) << 7); ctab = sat - 0x200; spt = (r[6] & 7) << 11
        size = 16 if r[1] & 2 else 8
        mag = 2 if r[1] & 1 else 1
        ents = []
        for i in range(32):
            y, x, n, _ = v[sat + i * 4: sat + i * 4 + 4]
            if y == 216: break
            ents.append((i, y, x, n & (0xFC if size == 16 else 0xFF)))
        s.over = 0
        for Y in range(192):
            line = []
            for i, y, x, n in ents:
                top = (y + 1) & 0xFF
                if top > 0xE0: top -= 256
                row = (Y - top) // mag if Y >= top else -1
                if 0 <= row < size:
                    line.append((i, x, n, row))
            if len(line) > 8: s.over += 1; line = line[:8]
            buf = {}; group = -1
            for i, x, n, row in line:
                cb = v[ctab + i * 16 + row]; col = cb & 15; cc = cb & 0x40; ec = cb & 0x80
                if not cc: group = i
                xx = x - 32 if ec else x
                for px_ in range(size * mag):
                    cx = px_ // mag
                    b = v[spt + n * 8 + (row & 7) + (16 if cx >= 8 else 0) + (8 if row >= 8 else 0)]
                    if not b & (0x80 >> (cx & 7)): continue
                    X = xx + px_
                    if not 0 <= X < 256: continue
                    if cc:
                        if X in buf and buf[X][1] == group: buf[X] = (buf[X][0] | col, group)
                        elif X not in buf: buf[X] = (col, group)
                    elif X not in buf: buf[X] = (col, i)
            for X, (col, _) in buf.items():
                if col: px[X, Y] = P[col]
        return im


class Cart2(romtest.CartMSX):
    def __init__(s, rom, seed=1):
        super().__init__(rom, seed); s.vdp = VDP2()
    def rd(s, a):
        a &= 0xFFFF; sl = (s.ppi_a >> ((a >> 14) * 2)) & 3
        if sl == 1 and 0x4000 <= a < 0xC000:
            p = a >> 14; return s.rom[(s.bank[p] * 0x4000 + (a & 0x3FFF)) % len(s.rom)]
        return MSX.rd(s, a)
    def wr(s, a, v):
        a &= 0xFFFF; sl = (s.ppi_a >> ((a >> 14) * 2)) & 3
        if sl == 1 and 0x4000 <= a < 0xC000:
            nb = len(s.rom) // 0x4000
            if 0x6000 <= a < 0x6800: s.bank[1] = v % nb
            elif 0x7000 <= a < 0x7800: s.bank[2] = v % nb
            return
        MSX.wr(s, a, v)


def boot2(rom, seed=1):
    m = Cart2(rom, seed); c = Z80(m); install_bios(c)
    _outp = c.outp
    def outp(p, v):
        if (p & 255) == 0x9A: m.vdp.wpal(v)
        else: _outp(p, v)
    c.outp = outp
    def chgmod(cpu):
        v = m.vdp; mode = cpu.A
        regs = {2: [0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x11],
                4: [0x04, 0xE0, 0x06, 0xFF, 0x03, 0x3F, 0x07, 0x11]}[mode]
        v.reg[:8] = regs
        for i in range(768): v.vram[0x1800 + i] = i & 255
        v.vram[0x1B00 if mode == 2 else 0x1E00] = 0xD0 if mode == 2 else 0xD8
        cpu.PC = cpu.pop(); return True
    c.hooks[0x5F] = chgmod
    m.ram[0x002D] = 1                         # version MSX2 (la BIOS simulada lee de RAM en pagina 0)
    m.ram[0xFEE4] = 0xC9; m.ram[0xFD9F] = 0xC9; m.ram[0xFD9A] = 0xC9
    m.ram[0xFCC1:0xFCC9] = b'\0' * 8
    m.ppi_a = (3 << 6) | (0 << 4) | (1 << 2) | 0
    c.SP = 0xF380; c.im = 1; c.iff = 0
    init = rom[2] | rom[3] << 8
    c.push(0x0000); c.PC = init
    return m, c
