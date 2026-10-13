"""Emulador MSX2 para la version SCREEN 5: VDP V9938 con G2 (tablas reubicables), G3, G4 (SCREEN 5),
registros 0-46, acceso indirecto (puerto 9Bh), estados S#0-S#2, banco R14, motor de comandos
(HMMC YMMM HMMM HMMV LMMC LMCM LMMM LMMV PSET POINT) con duracion aproximada (como WebMSX), e
interrupcion de VBLANK por nivel (se repite mientras no se lea S#0)."""
import os
from msx import *
import msx
from msx2emu import DEFPAL, Cart2
import msx2emu


class VDP5(msx2emu.VDP2):
    def __init__(s):
        super().__init__()
        s.cpu = None; s.ce_end = 0; s.cmd = 0; s.xfer = None; s.st1 = 0; s.cmdlog = None
        s.reg[15] = 0
        s.busy_wait = 0             # ciclos de CPU que el programa espera con CE=1 (estadistica)

    # ---------------- puertos ----------------
    def wctrl(s, v):
        if s.latch is None: s.latch = v; return
        lo = s.latch; s.latch = None
        if v & 0x80:
            s.wreg(v & 0x3F, lo)
        else:
            s.addr = ((v & 0x3F) << 8) | lo; s.hi = s.reg[14] & 7
            if not v & 0x40:
                s.rbuf = s.vram[s.hi << 14 | s.addr]; s.inc()
    def inc(s):
        s.addr = (s.addr + 1) & 0x3FFF
        if s.addr == 0 and s.mode() in ('G4', 'G5', 'G6', 'G7'):
            s.hi = (s.hi + 1) & 7; s.reg[14] = s.hi
    def wdata(s, v):
        s.latch = None
        a = s.hi << 14 | s.addr
        if s.log is not None: s.log(a, v)
        s.vram[a] = v; s.rbuf = v; s.inc()
    def rdata(s):
        s.latch = None; v = s.rbuf; s.rbuf = s.vram[s.hi << 14 | s.addr]; s.inc(); return v
    def wind(s, v):           # puerto 9Bh
        r = s.reg[17] & 0x3F
        if r != 17: s.wreg(r, v)
        if not s.reg[17] & 0x80: s.reg[17] = (s.reg[17] & 0xC0) | ((r + 1) & 0x3F)
    def wreg(s, r, v):
        if r >= 47: return
        s.reg[r] = v
        if r == 16: s.plat = None
        if r == 14: s.hi = v & 7
        if r == 44 and s.xfer is not None: s.xfer(v)
        if r == 46: s.start_cmd(v)
    def rstat(s):
        s.latch = None; n = s.reg[15] & 15
        if n == 0:
            v = s.stat; s.stat &= 0x1F; return v
        if n == 1:
            v = s.st1; s.st1 &= 0xFE; return v
        if n == 2:
            ce = s.ce()
            if ce and s.cpu is not None: s.busy_wait += 1
            return 0x8C | (0x80 if True else 0) | (1 if ce else 0) | (0x40 if s.in_vblank() else 0)
        if n == 7: return s.reg[44]
        return 0
    def in_vblank(s):
        if s.cpu is None: return False
        ph = (s.cpu.cyc - (s.cpu.next_int - msx.FRAME)) / msx.FRAME
        return ph < (msx.FRAME - 192 * 228) / msx.FRAME
    def ce(s):
        if s.xfer is not None: return True
        return s.cpu is not None and s.cpu.cyc < s.ce_end

    # ---------------- modo ----------------
    def mode(s):
        r = s.reg; m1 = (r[1] >> 4) & 1; m2 = (r[1] >> 3) & 1; m3 = (r[0] >> 1) & 1; m4 = (r[0] >> 2) & 1; m5 = (r[0] >> 3) & 1
        k = (m5, m4, m3, m2, m1)
        return {(0, 0, 0, 0, 1): 'T1', (0, 0, 0, 0, 0): 'G1', (0, 0, 1, 0, 0): 'G2', (0, 1, 0, 0, 0): 'G3',
                (0, 1, 1, 0, 0): 'G4', (1, 0, 0, 0, 0): 'G5', (1, 0, 1, 0, 0): 'G6', (1, 1, 1, 0, 0): 'G7'}.get(k, '?')

    # ---------------- comandos ----------------
    def g(s, lo, n=9):
        return (s.reg[lo] | s.reg[lo + 1] << 8) & ((1 << n) - 1)
    def setreg16(s, lo, v):
        s.reg[lo] = v & 255; s.reg[lo + 1] = (v >> 8) & 3
    def paddr(s, x, y): return ((y & 1023) * 128 + ((x & 255) >> 1)) & 0x1FFFF
    def pget(s, x, y):
        b = s.vram[s.paddr(x, y)]; return (b >> 4) if not x & 1 else (b & 15)
    def pset(s, x, y, c, lop):
        a = s.paddr(x, y); b = s.vram[a]; d = (b >> 4) if not x & 1 else (b & 15)
        if lop & 8 and c == 0: return
        op = lop & 7
        if op == 0: n = c
        elif op == 1: n = d & c
        elif op == 2: n = d | c
        elif op == 3: n = d ^ c
        elif op == 4: n = (~c) & 15
        else: n = d
        s.vram[a] = ((n << 4) | (b & 15)) if not x & 1 else ((b & 0xF0) | n)
    def busy(s, cycles):
        cpu = s.cpu
        if cpu is None: return
        s.ce_end = cpu.cyc + int(cycles / 6)
    def start_cmd(s, v):
        r = s.reg; op = v >> 4; lop = v & 15; s.xfer = None
        if s.mode() != 'G4':
            if op: s.busy(1000)
            return
        sx = s.g(32); sy = s.g(34, 10); dx = s.g(36); dy = s.g(38, 10); nx = s.g(40) or 512; ny = s.g(42, 10) or 1024
        arg = r[45]; dix = -1 if arg & 4 else 1; diy = -1 if arg & 8 else 1
        if s.cmdlog is not None: s.cmdlog((op, lop, sx, sy, dx, dy, nx, ny, arg, r[44]))
        if op == 0:
            s.ce_end = 0; return
        if op in (0xD, 0xC, 0xE, 0xF):          # comandos de byte (2 px)
            sxb, dxb, nxb = sx >> 1, dx >> 1, max(1, nx >> 1)
            if op == 0xD:                         # HMMM
                for j in range(ny):
                    for i in range(nxb):
                        X = (dxb + dix * i) & 127; SX = (sxb + dix * i) & 127
                        s.vram[((dy + diy * j) & 1023) * 128 + X] = s.vram[((sy + diy * j) & 1023) * 128 + SX]
                s.setreg16(34, sy + diy * ny); s.setreg16(38, dy + diy * ny)
                s.busy(nxb * ny * 88 * 1.1 + ny * 64)
            elif op == 0xC:                       # HMMV
                for j in range(ny):
                    for i in range(nxb):
                        s.vram[((dy + diy * j) & 1023) * 128 + ((dxb + dix * i) & 127)] = r[44]
                s.setreg16(38, dy + diy * ny)
                s.busy(nxb * ny * 48 * 1.1 + ny * 56)
            elif op == 0xE:                       # YMMM
                w = (128 - dxb) if dix == 1 else dxb + 1
                for j in range(ny):
                    for i in range(w):
                        X = (dxb + dix * i) & 127
                        s.vram[((dy + diy * j) & 1023) * 128 + X] = s.vram[((sy + diy * j) & 1023) * 128 + X]
                s.setreg16(34, sy + diy * ny); s.setreg16(38, dy + diy * ny)
                s.busy(w * ny * 64 * 1.1)
            else:                                 # HMMC
                st = {'i': 0, 'j': 0}
                def put(b):
                    i, j = st['i'], st['j']
                    s.vram[((dy + diy * j) & 1023) * 128 + ((dxb + dix * i) & 127)] = b
                    i += 1
                    if i >= nxb: i = 0; j += 1
                    st['i'], st['j'] = i, j
                    if j >= ny: s.xfer = None; s.ce_end = 0
                s.xfer = put; put(r[44])
            return
        if op == 0x9:                             # LMMM
            for j in range(ny):
                for i in range(nx):
                    s.pset(dx + dix * i, dy + diy * j, s.pget(sx + dix * i, sy + diy * j), lop)
            s.setreg16(34, sy + diy * ny); s.setreg16(38, dy + diy * ny)
            s.busy(nx * ny * 120 * 1.1 + ny * 64)
        elif op == 0x8:                           # LMMV
            for j in range(ny):
                for i in range(nx):
                    s.pset(dx + dix * i, dy + diy * j, r[44] & 15, lop)
            s.setreg16(38, dy + diy * ny)
            s.busy(nx * ny * 96 * 1.1 + ny * 64)
        elif op == 0xB:                           # LMMC
            st = {'i': 0, 'j': 0}
            def put(b):
                i, j = st['i'], st['j']
                s.pset(dx + dix * i, dy + diy * j, b & 15, lop)
                i += 1
                if i >= nx: i = 0; j += 1
                st['i'], st['j'] = i, j
                if j >= ny: s.xfer = None; s.ce_end = 0
            s.xfer = put; put(r[44])
        elif op == 0x5:                           # PSET
            s.pset(dx, dy, r[44] & 15, lop); s.busy(100)
        elif op == 0x4:                           # POINT
            r[44] = s.pget(sx, sy); s.busy(100)
        else:
            s.busy(2000)

    # ---------------- imagen ----------------
    def render(s, sprites=True, lines=192):
        r = s.reg; v = s.vram
        P = [s.rgb(i) for i in range(16)]
        bd = r[7] & 15
        mode = s.mode()
        im = Image.new('RGB', (256, lines), P[bd]); px = im.load()
        if not (r[1] & 0x40): return im
        tp = r[8] & 0x20
        if mode == 'G4':
            base = ((r[2] >> 5) & 3) * 0x8000
            for y in range(lines):
                row = base + ((y + r[23]) & 255) * 128
                for xb in range(128):
                    b = v[row + xb]
                    for k, c in ((0, b >> 4), (1, b & 15)):
                        if c == 0 and not tp: c = bd
                        px[xb * 2 + k, y] = P[c]
            return im
        if mode in ('G2', 'G3'):
            nt = (r[2] & 0x7F) << 10
            ct = ((r[10] & 7) << 14) | ((r[3] & 0x80) << 6)
            pt = (r[4] & 0x3C) << 11
            for y in range(min(lines, 192)):
                third = y >> 6
                for tx in range(32):
                    ch = v[nt + (y >> 3) * 32 + tx] + third * 256
                    p = v[pt + ch * 8 + (y & 7)]; c = v[ct + ch * 8 + (y & 7)]
                    fg, bg = c >> 4, c & 15
                    for k in range(8):
                        col = fg if p & (0x80 >> k) else bg
                        if col == 0 and not tp: col = bd
                        px[tx * 8 + k, y] = P[col]
            return im
        return im


class Z80L(Z80):
    """IRQ por nivel (VBLANK hasta leer S#0) con el retardo de una instruccion tras EI."""
    def __init__(s, m):
        super().__init__(m); s.ei_wait = False
    def step(s):
        m = s.m
        if s.cyc >= s.next_int:
            s.next_int += msx.FRAME; m.vdp.stat |= 0x80; s.frames += 1
            if s.on_frame: s.on_frame(s)
        if s.iff and not s.ei_wait and (m.vdp.reg[1] & 0x20) and (m.vdp.stat & 0x80):
            s.iff = 0; s.halt = False
            s.push(s.PC)
            if s.im == 2:
                vv = (s.I << 8) | 0xFF; s.PC = m.rd(vv) | m.rd(vv + 1) << 8
            else: s.PC = 0x38
            s.cyc += 19
        s.ei_wait = False
        pc = s.PC
        h = s.hooks.get(pc)
        if h is not None and m.slot(pc >> 14) == 0 and h(s): return
        if s.halt: s.cyc += 5 if msx.TIMED else 4; return
        op = m.rd(pc)
        if msx.TIMED:
            c0 = s.cyc; s._ins(); s.cyc = c0 + tstates(s, pc)
        else:
            s._ins()
        if op == 0xFB: s.ei_wait = True


class Cart5(Cart2):
    def __init__(s, rom, seed=1):
        super().__init__(rom, seed); s.vdp = VDP5()


def boot5(rom, seed=1):
    m = Cart5(rom, seed); c = Z80L(m); install_bios(c); m.vdp.cpu = c
    _outp = c.outp
    def outp(p, v):
        p &= 255
        if p == 0x9A: m.vdp.wpal(v)
        elif p == 0x9B: m.vdp.wind(v)
        else: _outp(p, v)
    c.outp = outp
    def chgmod(cpu):
        v = m.vdp; mode = cpu.A
        regs = {2: [0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x11],
                4: [0x04, 0xE0, 0x06, 0xFF, 0x03, 0x3F, 0x07, 0x11],
                5: [0x06, 0x60, 0x1F, 0x00, 0x00, 0xEF, 0x0F, 0x11]}[mode]
        v.reg[:8] = regs
        if mode in (2, 4):
            for i in range(768): v.vram[0x1800 + i] = i & 255
        cpu.PC = cpu.pop(); return True
    c.hooks[0x5F] = chgmod
    def keyint(cpu):
        m.vdp.rstat(); cpu.iff = 1; cpu.PC = cpu.pop(); return True
    c.hooks[0x38] = keyint
    m.ram[0x002D] = 1
    m.ram[0xFFE8] = 0x02 if msx.FRAME > 65000 else 0x00
    m.ram[0xFEE4] = 0xC9; m.ram[0xFD9F] = 0xC9; m.ram[0xFD9A] = 0xC9
    m.ram[0xFCC1:0xFCC9] = b'\0' * 8
    m.ppi_a = (3 << 6) | (0 << 4) | (1 << 2) | 0
    c.SP = 0xF380; c.im = 1; c.iff = 0
    init = rom[2] | rom[3] << 8
    c.push(0x0000); c.PC = init
    return m, c
