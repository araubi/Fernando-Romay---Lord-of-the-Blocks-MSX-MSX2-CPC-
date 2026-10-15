"""Emulador MSX1 minimo para depurar: Z80 (documentado), slots, VDP TMS9918 (SCREEN 2 + sprites),
BIOS simulada por ganchos. Pensado para observar el juego, no para ser exacto en tiempos."""
import os
FRAME = int(os.environ.get('MSX_FRAME', '59659'))
import random
from PIL import Image

S_, Z_, H_, P_, N_, C_ = 0x80, 0x40, 0x10, 0x04, 0x02, 0x01
PAR = [bin(i).count('1') % 2 == 0 for i in range(256)]
PAL = [(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),
       (252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]

class VDP:
    def __init__(s):
        s.vram = bytearray(16384); s.reg = [0] * 8; s.addr = 0; s.latch = None; s.stat = 0
        s.rbuf = 0; s.log = None; s.pc = 0
    def wctrl(s, v):
        if s.latch is None: s.latch = v; return
        lo = s.latch; s.latch = None
        if v & 0x80: s.reg[v & 7] = lo
        else:
            s.addr = ((v & 0x3F) << 8) | lo
            if not v & 0x40: s.rbuf = s.vram[s.addr]; s.addr = (s.addr + 1) & 0x3FFF
    def wdata(s, v):
        s.latch = None
        if s.log is not None: s.log(s.addr, v)
        s.vram[s.addr] = v; s.rbuf = v; s.addr = (s.addr + 1) & 0x3FFF
    def rdata(s):
        s.latch = None; v = s.rbuf; s.rbuf = s.vram[s.addr]; s.addr = (s.addr + 1) & 0x3FFF; return v
    def rstat(s):
        s.latch = None; v = s.stat; s.stat &= 0x1F; return v
    def render(s, sprites=True):
        r = s.reg; v = s.vram
        im = Image.new('RGB', (256, 192), PAL[r[7] & 15]); px = im.load()
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
                    px[tx * 8 + k, y] = PAL[col]
        if sprites:
            sat = (r[5] & 0x7F) << 7; spt = (r[6] & 7) << 11
            big = r[1] & 2; mag = 2 if r[1] & 1 else 1; size = 16 if big else 8
            lst = []
            for i in range(32):
                y, x, n, c = v[sat + i * 4: sat + i * 4 + 4]
                if y == 208: break
                lst.append((i, y, x, n, c))
            for i, y, x, n, c in reversed(lst):
                if c & 15 == 0: continue
                if c & 0x80: x -= 32
                y = (y + 1) & 0xFF
                if y > 0xE0: y -= 256
                if big: n &= 0xFC
                for row in range(size):
                    for col in range(size):
                        b = v[spt + n * 8 + (row & 7) + (16 if col >= 8 else 0) + (8 if row >= 8 else 0)]
                        if b & (0x80 >> (col & 7)):
                            for my in range(mag):
                                for mx in range(mag):
                                    X = x + col * mag + mx; Y = y + row * mag + my
                                    if 0 <= X < 256 and 0 <= Y < 192: px[X, Y] = PAL[c & 15]
        return im

class MSX:
    def __init__(s, seed=1):
        rnd = random.Random(seed)
        s.ram = bytearray(rnd.randrange(256) for _ in range(65536))
        s.ppi_a = 0xF0; s.ppi_c = 0; s.keys = [0xFF] * 11; s.vdp = VDP()
        s.joy = 0x3F
        # sistema: EXPTBL 0 (no expandido), RAM en slot 3
        s.ram[0xFCC1:0xFCC9] = b'\0' * 8
    def slot(s, page): return (s.ppi_a >> (page * 2)) & 3
    def rd(s, a):
        a &= 0xFFFF
        sl = (s.ppi_a >> ((a >> 14) * 2)) & 3
        if sl == 3: return s.ram[a]
        if sl == 0 and a < 0x8000:
            if a in (6, 7): return 0x98
            return 0xC9
        return 0xFF
    def wr(s, a, v):
        a &= 0xFFFF
        if (s.ppi_a >> ((a >> 14) * 2)) & 3 == 3: s.ram[a] = v & 0xFF

import os as _os
TIMED = bool(_os.environ.get('MSX_TIMED'))
from ztiming import tstates
class Z80:
    def __init__(s, m):
        s.m = m; s.A = s.F = s.B = s.C = s.D = s.E = s.H = s.L = 0
        s.IX = s.IY = 0; s.SP = 0xF000; s.PC = 0; s.sh = [0] * 8
        s.I = 0; s.R = 0; s.iff = 0; s.im = 1; s.halt = False
        s.cyc = 0; s.next_int = FRAME; s.hooks = {}; s.frames = 0; s.ring = []
        s.on_frame = None
    # --- registros dobles ---
    def gHL(s): return s.H << 8 | s.L
    def sHL(s, v): s.H = (v >> 8) & 255; s.L = v & 255
    def gBC(s): return s.B << 8 | s.C
    def sBC(s, v): s.B = (v >> 8) & 255; s.C = v & 255
    def gDE(s): return s.D << 8 | s.E
    def sDE(s, v): s.D = (v >> 8) & 255; s.E = v & 255
    def rp(s, i, ix=None):
        if i == 0: return s.gBC()
        if i == 1: return s.gDE()
        if i == 2: return s.gHL() if ix is None else (s.IX if ix == 'X' else s.IY)
        return s.SP
    def srp(s, i, v, ix=None):
        v &= 0xFFFF
        if i == 0: s.sBC(v)
        elif i == 1: s.sDE(v)
        elif i == 2:
            if ix is None: s.sHL(v)
            elif ix == 'X': s.IX = v
            else: s.IY = v
        else: s.SP = v
    def r8(s, i): return (s.B, s.C, s.D, s.E, s.H, s.L, 0, s.A)[i]
    def w8(s, i, v):
        v &= 255
        if i == 0: s.B = v
        elif i == 1: s.C = v
        elif i == 2: s.D = v
        elif i == 3: s.E = v
        elif i == 4: s.H = v
        elif i == 5: s.L = v
        elif i == 7: s.A = v
    def ea(s, ix, d):
        if ix is None: return s.gHL()
        return ((s.IX if ix == 'X' else s.IY) + (d - 256 if d > 127 else d)) & 0xFFFF
    def get(s, i, ix=None, d=0):
        if i == 6: return s.m.rd(s.ea(ix, d))
        if ix is not None and i in (4, 5):
            v = s.IX if ix == 'X' else s.IY
            return (v >> 8) & 255 if i == 4 else v & 255
        return s.r8(i)
    def put(s, i, v, ix=None, d=0):
        if i == 6: s.m.wr(s.ea(ix, d), v & 255); return
        if ix is not None and i in (4, 5):
            cur = s.IX if ix == 'X' else s.IY
            cur = (cur & 0xFF) | (v & 255) << 8 if i == 4 else (cur & 0xFF00) | (v & 255)
            if ix == 'X': s.IX = cur
            else: s.IY = cur
            return
        s.w8(i, v)
    def fetch(s):
        v = s.m.rd(s.PC); s.PC = (s.PC + 1) & 0xFFFF; return v
    def f16(s):
        lo = s.fetch(); return lo | s.fetch() << 8
    def push(s, v):
        s.SP = (s.SP - 1) & 0xFFFF; s.m.wr(s.SP, (v >> 8) & 255)
        s.SP = (s.SP - 1) & 0xFFFF; s.m.wr(s.SP, v & 255)
    def pop(s):
        lo = s.m.rd(s.SP); hi = s.m.rd(s.SP + 1); s.SP = (s.SP + 2) & 0xFFFF; return lo | hi << 8
    def cc(s, i):
        f = s.F
        return (not f & Z_, bool(f & Z_), not f & C_, bool(f & C_), not f & P_, bool(f & P_), not f & S_, bool(f & S_))[i]
    # --- ALU ---
    def alu(s, op, v):
        a = s.A
        if op <= 1:
            c = s.F & C_ if op == 1 else 0; r = a + v + c
            s.A = r & 255
            s.F = (s.A & S_) | (Z_ if not s.A else 0) | (H_ if (a & 15) + (v & 15) + c > 15 else 0) | \
                  (P_ if (~(a ^ v) & (a ^ r) & 0x80) else 0) | (C_ if r > 255 else 0)
        elif op in (2, 3, 7):
            c = s.F & C_ if op == 3 else 0; r = a - v - c; res = r & 255
            f = (res & S_) | (Z_ if not res else 0) | (H_ if (a & 15) - (v & 15) - c < 0 else 0) | \
                (P_ if ((a ^ v) & (a ^ r) & 0x80) else 0) | N_ | (C_ if r < 0 else 0)
            if op != 7: s.A = res
            s.F = f
        elif op == 4: s.A = a & v; s.F = (s.A & S_) | (Z_ if not s.A else 0) | H_ | (P_ if PAR[s.A] else 0)
        elif op == 5: s.A = a ^ v; s.F = (s.A & S_) | (Z_ if not s.A else 0) | (P_ if PAR[s.A] else 0)
        else: s.A = a | v; s.F = (s.A & S_) | (Z_ if not s.A else 0) | (P_ if PAR[s.A] else 0)
    def inc8(s, v):
        r = (v + 1) & 255
        s.F = (s.F & C_) | (r & S_) | (Z_ if not r else 0) | (H_ if v & 15 == 15 else 0) | (P_ if v == 0x7F else 0); return r
    def dec8(s, v):
        r = (v - 1) & 255
        s.F = (s.F & C_) | (r & S_) | (Z_ if not r else 0) | (H_ if v & 15 == 0 else 0) | (P_ if v == 0x80 else 0) | N_; return r
    def add16(s, a, b):
        r = a + b
        s.F = (s.F & (S_ | Z_ | P_)) | (H_ if (a & 0xFFF) + (b & 0xFFF) > 0xFFF else 0) | (C_ if r > 0xFFFF else 0)
        return r & 0xFFFF
    def adc16(s, b):
        a = s.gHL(); c = s.F & C_; r = a + b + c; res = r & 0xFFFF
        s.F = ((res >> 8) & S_) | (Z_ if not res else 0) | (H_ if (a & 0xFFF) + (b & 0xFFF) + c > 0xFFF else 0) | \
              (P_ if (~(a ^ b) & (a ^ r) & 0x8000) else 0) | (C_ if r > 0xFFFF else 0)
        s.sHL(res)
    def sbc16(s, b):
        a = s.gHL(); c = s.F & C_; r = a - b - c; res = r & 0xFFFF
        s.F = ((res >> 8) & S_) | (Z_ if not res else 0) | (H_ if (a & 0xFFF) - (b & 0xFFF) - c < 0 else 0) | \
              (P_ if ((a ^ b) & (a ^ r) & 0x8000) else 0) | N_ | (C_ if r < 0 else 0)
        s.sHL(res)
    def rot(s, y, v):
        c = s.F & C_
        if y == 0: r = ((v << 1) | (v >> 7)) & 255; co = v >> 7
        elif y == 1: r = ((v >> 1) | (v << 7)) & 255; co = v & 1
        elif y == 2: r = ((v << 1) | c) & 255; co = v >> 7
        elif y == 3: r = (v >> 1) | (c << 7); co = v & 1
        elif y == 4: r = (v << 1) & 255; co = v >> 7
        elif y == 5: r = (v >> 1) | (v & 0x80); co = v & 1
        elif y == 6: r = ((v << 1) | 1) & 255; co = v >> 7
        else: r = v >> 1; co = v & 1
        s.F = (r & S_) | (Z_ if not r else 0) | (P_ if PAR[r] else 0) | co; return r
    # --- E/S ---
    def inp(s, p):
        p &= 255; m = s.m
        if p == 0x98: return m.vdp.rdata()
        if p == 0x99: return m.vdp.rstat()
        if p == 0xA8: return m.ppi_a
        if p == 0xA9: return m.keys[m.ppi_c & 15] if (m.ppi_c & 15) < 11 else 0xFF
        if p == 0xAA: return m.ppi_c
        if p == 0xA2: return m.joy
        return 0xFF
    def outp(s, p, v):
        p &= 255; m = s.m
        if p == 0x98: m.vdp.pc = s.PC; m.vdp.wdata(v)
        elif p == 0x99: m.vdp.wctrl(v)
        elif p == 0xA8: m.ppi_a = v
        elif p == 0xAA: m.ppi_c = v
        elif p == 0xAB:
            if not v & 0x80:
                bit = (v >> 1) & 7
                m.ppi_c = (m.ppi_c | (1 << bit)) if v & 1 else (m.ppi_c & ~(1 << bit))
    # --- ejecucion ---
    def run(s, n=1 << 60, until=None):
        for _ in range(n):
            if until is not None and s.PC == until: return True
            s.step()
        return False
    def step(s):
        m = s.m
        if s.cyc >= s.next_int:
            s.next_int += FRAME; m.vdp.stat |= 0x80; s.frames += 1
            if s.on_frame: s.on_frame(s)
            if s.iff and (m.vdp.reg[1] & 0x20):
                s.iff = 0; s.halt = False
                s.push(s.PC)
                if s.im == 2:
                    v = (s.I << 8) | 0xFF; s.PC = m.rd(v) | m.rd(v + 1) << 8
                else: s.PC = 0x38
        pc = s.PC
        h = s.hooks.get(pc)
        if h is not None and m.slot(pc >> 14) == 0 and h(s): return
        if s.halt: s.cyc += 5 if TIMED else 4; return
        if TIMED:
            c0 = s.cyc; s._ins(); s.cyc = c0 + tstates(s, pc); return
        s._ins()
    def _ins(s):
        m = s.m
        op = s.fetch(); s.cyc += 5; s.R = (s.R + 1) & 127
        ix = None
        if op == 0xDD or op == 0xFD:
            ix = 'X' if op == 0xDD else 'Y'; op = s.fetch(); s.cyc += 4
            if op in (0xDD, 0xFD, 0xED): s.PC = (s.PC - 1) & 0xFFFF; return
        if op == 0xED: return s.ed()
        if op == 0xCB: return s.cb(ix)
        x, y, z = op >> 6, (op >> 3) & 7, op & 7; p, q = y >> 1, y & 1
        if x == 0:
            if z == 0:
                if y == 0: pass
                elif y == 1:
                    s.A, s.sh[0] = s.sh[0], s.A; s.F, s.sh[1] = s.sh[1], s.F
                else:
                    d = s.fetch(); d = d - 256 if d > 127 else d
                    if y == 2:
                        s.B = (s.B - 1) & 255
                        if s.B: s.PC = (s.PC + d) & 0xFFFF
                    elif y == 3 or s.cc(y - 4): s.PC = (s.PC + d) & 0xFFFF
            elif z == 1:
                if q == 0: s.srp(p, s.f16(), ix)
                else: s.srp(2, s.add16(s.rp(2, ix), s.rp(p, ix)), ix)
            elif z == 2:
                if p == 0:
                    if q == 0: m.wr(s.gBC(), s.A)
                    else: s.A = m.rd(s.gBC())
                elif p == 1:
                    if q == 0: m.wr(s.gDE(), s.A)
                    else: s.A = m.rd(s.gDE())
                else:
                    nn = s.f16()
                    if p == 2:
                        if q == 0: v = s.rp(2, ix); m.wr(nn, v & 255); m.wr(nn + 1, v >> 8)
                        else: s.srp(2, m.rd(nn) | m.rd(nn + 1) << 8, ix)
                    else:
                        if q == 0: m.wr(nn, s.A)
                        else: s.A = m.rd(nn)
            elif z == 3: s.srp(p, s.rp(p, ix) + (1 if q == 0 else -1), ix)
            elif z <= 5:
                d = s.fetch() if (y == 6 and ix) else 0
                v = s.get(y, ix, d); s.put(y, s.inc8(v) if z == 4 else s.dec8(v), ix, d)
            elif z == 6:
                d = s.fetch() if (y == 6 and ix) else 0
                s.put(y, s.fetch(), ix, d)
            else:
                a = s.A
                if y == 0: s.A = ((a << 1) | (a >> 7)) & 255; s.F = (s.F & 0xC4) | (a >> 7)
                elif y == 1: s.A = ((a >> 1) | (a << 7)) & 255; s.F = (s.F & 0xC4) | (a & 1)
                elif y == 2: s.A = ((a << 1) | (s.F & 1)) & 255; s.F = (s.F & 0xC4) | (a >> 7)
                elif y == 3: s.A = (a >> 1) | ((s.F & 1) << 7); s.F = (s.F & 0xC4) | (a & 1)
                elif y == 4:
                    nf = s.F & N_; c = s.F & C_; adj = 0
                    if s.F & H_ or (a & 15) > 9: adj |= 6
                    if c or a > 0x99: adj |= 0x60; c = C_
                    r = (a - adj if nf else a + adj) & 255
                    hf = ((a & 15) - (adj & 15) < 0) if nf else ((a & 15) + (adj & 15) > 15)
                    s.A = r; s.F = (r & S_) | (Z_ if not r else 0) | (H_ if hf else 0) | (P_ if PAR[r] else 0) | nf | c
                elif y == 5: s.A = a ^ 255; s.F |= H_ | N_
                elif y == 6: s.F = (s.F & 0xC4) | C_
                else: s.F = (s.F & 0xC4) | (H_ if s.F & C_ else 0) | (0 if s.F & C_ else C_)
        elif x == 1:
            if op == 0x76: s.halt = True; return
            if y == 6 or z == 6:
                d = s.fetch() if ix else 0
                if y == 6: m.wr(s.ea(ix, d), s.r8(z))
                else: s.w8(y, m.rd(s.ea(ix, d)))
            else: s.put(y, s.get(z, ix), ix)
        elif x == 2:
            d = s.fetch() if (z == 6 and ix) else 0
            s.alu(y, s.get(z, ix, d))
        else:
            if z == 0:
                if s.cc(y): s.PC = s.pop()
            elif z == 1:
                if q == 0:
                    v = s.pop()
                    if p == 3: s.A = v >> 8; s.F = v & 255
                    else: s.srp(p, v, ix)
                elif p == 0: s.PC = s.pop()
                elif p == 1:
                    s.B, s.sh[2] = s.sh[2], s.B; s.C, s.sh[3] = s.sh[3], s.C; s.D, s.sh[4] = s.sh[4], s.D
                    s.E, s.sh[5] = s.sh[5], s.E; s.H, s.sh[6] = s.sh[6], s.H; s.L, s.sh[7] = s.sh[7], s.L
                elif p == 2: s.PC = s.rp(2, ix)
                else: s.SP = s.rp(2, ix)
            elif z == 2:
                nn = s.f16()
                if s.cc(y): s.PC = nn
            elif z == 3:
                if y == 0: s.PC = s.f16()
                elif y == 2: s.outp(s.A << 8 | s.fetch(), s.A)
                elif y == 3: s.A = s.inp(s.A << 8 | s.fetch())
                elif y == 4: v = s.pop(); s.push(s.rp(2, ix)); s.srp(2, v, ix)
                elif y == 5: h_ = s.gHL(); s.sHL(s.gDE()); s.sDE(h_)
                elif y == 6: s.iff = 0
                else: s.iff = 1
            elif z == 4:
                nn = s.f16()
                if s.cc(y): s.push(s.PC); s.PC = nn
            elif z == 5:
                if q == 0: s.push((s.A << 8 | s.F) if p == 3 else s.rp(p, ix))
                else: nn = s.f16(); s.push(s.PC); s.PC = nn
            elif z == 6: s.alu(y, s.fetch())
            else: s.push(s.PC); s.PC = y * 8
    def cb(s, ix):
        if ix:
            d = s.fetch(); op = s.fetch(); a = s.ea(ix, d); v = s.m.rd(a)
        else:
            op = s.fetch(); v = s.get(op & 7)
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        if x == 1:
            s.F = (s.F & C_) | H_ | ((Z_ | P_) if not v & (1 << y) else 0) | (S_ if y == 7 and v & 0x80 else 0); return
        r = s.rot(y, v) if x == 0 else (v & ~(1 << y) if x == 2 else v | (1 << y))
        if ix:
            s.m.wr(a, r)
            if z != 6: s.w8(z, r)
        else: s.put(z, r)
    def ed(s):
        op = s.fetch(); x, y, z = op >> 6, (op >> 3) & 7, op & 7; p, q = y >> 1, y & 1; m = s.m
        if x == 1:
            if z == 0:
                v = s.inp(s.gBC())
                if y != 6: s.w8(y, v)
                s.F = (s.F & C_) | (v & S_) | (Z_ if not v else 0) | (P_ if PAR[v] else 0)
            elif z == 1: s.outp(s.gBC(), s.r8(y) if y != 6 else 0)
            elif z == 2: (s.sbc16 if q == 0 else s.adc16)(s.rp(p))
            elif z == 3:
                nn = s.f16()
                if q == 0: v = s.rp(p); m.wr(nn, v & 255); m.wr(nn + 1, v >> 8)
                else: s.srp(p, m.rd(nn) | m.rd(nn + 1) << 8)
            elif z == 4:
                a = s.A; r = (-a) & 255
                s.F = (r & S_) | (Z_ if not r else 0) | (H_ if a & 15 else 0) | (P_ if a == 0x80 else 0) | N_ | (C_ if a else 0)
                s.A = r
            elif z == 5: s.PC = s.pop(); s.iff = 1
            elif z == 6: s.im = (0, 0, 1, 2, 0, 0, 1, 2)[y]
            else:
                if y == 0: s.I = s.A
                elif y == 1: s.R = s.A
                elif y in (2, 3):
                    s.A = s.I if y == 2 else s.R
                    s.F = (s.F & C_) | (s.A & S_) | (Z_ if not s.A else 0) | (P_ if s.iff else 0)
                elif y == 4:
                    hv = m.rd(s.gHL()); a = s.A
                    m.wr(s.gHL(), ((a & 15) << 4) | (hv >> 4)); s.A = (a & 0xF0) | (hv & 15)
                    s.F = (s.F & C_) | (s.A & S_) | (Z_ if not s.A else 0) | (P_ if PAR[s.A] else 0)
                elif y == 5:
                    hv = m.rd(s.gHL()); a = s.A
                    m.wr(s.gHL(), ((hv << 4) & 0xF0) | (a & 15)); s.A = (a & 0xF0) | (hv >> 4)
                    s.F = (s.F & C_) | (s.A & S_) | (Z_ if not s.A else 0) | (P_ if PAR[s.A] else 0)
        elif x == 2 and z <= 3 and y >= 4:
            rep = y >= 6; d = -1 if y in (5, 7) else 1
            while True:
                if z == 0:
                    m.wr(s.gDE(), m.rd(s.gHL())); s.sHL(s.gHL() + d); s.sDE(s.gDE() + d); s.sBC(s.gBC() - 1)
                    s.F = (s.F & (S_ | Z_ | C_)) | (P_ if s.gBC() else 0); s.cyc += 21
                    if rep and s.gBC(): s.PC = (s.PC - 2) & 0xFFFF
                    break
                elif z == 1:
                    v = m.rd(s.gHL()); r = (s.A - v) & 255; s.sHL(s.gHL() + d); s.sBC(s.gBC() - 1)
                    s.F = (s.F & C_) | (r & S_) | (Z_ if not r else 0) | (H_ if (s.A & 15) < (v & 15) else 0) | (P_ if s.gBC() else 0) | N_
                    s.cyc += 21
                    if rep and s.gBC() and r: s.PC = (s.PC - 2) & 0xFFFF
                    break
                elif z == 2:
                    m.wr(s.gHL(), s.inp(s.gBC())); s.sHL(s.gHL() + d); s.B = (s.B - 1) & 255
                    s.F = (s.F & C_) | (Z_ if not s.B else 0) | N_; s.cyc += 21
                    if rep and s.B: s.PC = (s.PC - 2) & 0xFFFF
                    break
                else:
                    s.B = (s.B - 1) & 255; s.outp(s.gBC(), m.rd(s.gHL())); s.sHL(s.gHL() + d)
                    s.F = (s.F & C_) | (Z_ if not s.B else 0) | N_; s.cyc += 21
                    if rep and s.B: s.PC = (s.PC - 2) & 0xFFFF
                    break

# ---------------- BIOS simulada ----------------
def install_bios(c):
    m = c.m
    def ret(cpu): cpu.PC = cpu.pop(); return True
    def enaslt(cpu):
        page = cpu.H >> 6; sl = cpu.A & 3
        m.ppi_a = (m.ppi_a & ~(3 << (page * 2))) | (sl << (page * 2)); cpu.iff = 0; return ret(cpu)
    def rslreg(cpu): cpu.A = m.ppi_a; return ret(cpu)
    def snsmat(cpu): cpu.A = m.keys[cpu.A] if cpu.A < 11 else 0xFF; return ret(cpu)
    def gtstck(cpu):
        row8 = m.keys[8]; v = 0
        up, dn, lf, rt = not row8 & 0x20, not row8 & 0x40, not row8 & 0x10, not row8 & 0x80
        if cpu.A == 0:
            tbl = {(1,0,0,0):1,(1,0,0,1):2,(0,0,0,1):3,(0,1,0,1):4,(0,1,0,0):5,(0,1,1,0):6,(0,0,1,0):7,(1,0,1,0):8}
            v = tbl.get((int(up), int(dn), int(lf), int(rt)), 0)
        cpu.A = v; return ret(cpu)
    def gttrig(cpu): cpu.A = 0xFF if (cpu.A == 0 and not m.keys[8] & 1) else 0; return ret(cpu)
    def wrtvdp(cpu): m.vdp.reg[cpu.C & 7] = cpu.B; return ret(cpu)
    def setwrt(cpu): m.vdp.hi = 0; m.vdp.addr = cpu.gHL() & 0x3FFF; return ret(cpu)
    def setrd(cpu): m.vdp.hi = 0; m.vdp.addr = cpu.gHL() & 0x3FFF; return ret(cpu)
    def ldirvm(cpu):
        m.vdp.hi = 0
        for k in range(cpu.gBC()): m.vdp.pc = 0x5C; m.vdp.addr = (cpu.gDE() + k) & 0x3FFF; m.vdp.wdata(m.rd(cpu.gHL() + k))
        return ret(cpu)
    def filvrm(cpu):
        m.vdp.hi = 0
        for k in range(cpu.gBC()): m.vdp.addr = (cpu.gHL() + k) & 0x3FFF; m.vdp.wdata(cpu.A)
        return ret(cpu)
    def wrtvrm(cpu): m.vdp.hi = 0; m.vdp.addr = cpu.gHL() & 0x3FFF; m.vdp.wdata(cpu.A); return ret(cpu)
    def rdvrm(cpu): m.vdp.hi = 0; cpu.A = m.vdp.vram[cpu.gHL() & 0x3FFF]; return ret(cpu)
    def chput(cpu): c.text.append(cpu.A); return ret(cpu)
    def kilbuf(cpu): return ret(cpu)
    def chsns(cpu): cpu.F |= Z_; return ret(cpu)
    def rdpsg(cpu): cpu.A = 0xFF; return ret(cpu)
    def keyint(cpu):   # ISR de la BIOS (IM 1): marca VBLANK y vuelve
        m.vdp.rstat(); cpu.iff = 1; cpu.PC = cpu.pop(); return True
    c.text = []
    H = {0x24: enaslt, 0x138: rslreg, 0x141: snsmat, 0xD5: gtstck, 0xD8: gttrig, 0x47: wrtvdp, 0x53: setwrt,
         0x50: setrd, 0x5C: ldirvm, 0x56: filvrm, 0x4D: wrtvrm, 0x4A: rdvrm, 0xA2: chput, 0x156: kilbuf, 0x9C: chsns,
         0x38: keyint, 0x93: ret, 0x96: rdpsg, 0x90: ret, 0x41: ret, 0x44: ret, 0x6C: ret, 0x72: ret, 0x7E: ret,
         0xC0: ret, 0xC3: ret, 0x62: ret, 0x5F: ret, 0x69: ret, 0x132: ret, 0x135: ret, 0xF3: ret, 0xE7: ret}
    c.hooks.update(H)

# ---------------- carga de la cinta ----------------
def load_from_cas(cas_bytes, seed=1):
    """Reproduce: SCREEN 2 de BASIC y los tres BLOAD,R. Devuelve (maquina, cpu) parado en 84D0h."""
    from common import cas_blocks
    _, segs = cas_blocks(cas_bytes)
    files = []
    for ci in (3, 5, 7):
        c_ = segs[ci]; st = c_[0] | c_[1] << 8; en = c_[2] | c_[3] << 8; ex = c_[4] | c_[5] << 8
        files.append((st, en, ex, c_[6:6 + en - st + 1]))
    m = MSX(seed); c = Z80(m); install_bios(c)
    v = m.vdp
    v.reg = [0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x11]      # SCREEN 2, COLOR 1,1,1
    for i in range(768): v.vram[0x1800 + i] = i & 255
    v.vram[0x1B00] = 0xD0
    m.ram[0xF3E9:0xF3EC] = bytes([1, 1, 1])
    m.ram[0xFEE4] = 0xC9
    c.im = 1; c.iff = 1
    for st, en, ex, data in files:
        m.ram[st:st + len(data)] = data
        c.SP = 0x8300; c.push(0xFFF0); m.ram[0xFFF0] = 0x76; c.PC = ex
        if ex == 0x84D0: break
        ok = c.run(5_000_000, until=0xFFF0)
        assert ok, 'el stub de %04X no volvio' % ex
        c.iff = 1
    return m, c
