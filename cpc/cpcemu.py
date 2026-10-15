"""Emulador Amstrad CPC minimo para depurar el juego (sin ROMs: se carga el juego ya en memoria).
Z80 de z80core (MSX) con puertos de 16 bits; gate array, CRTC, PPI y teclado via PSG reg 14.
Tiempos aproximados: 256 T por linea, 312 lineas por cuadro, interrupcion cada 52 lineas."""
import numpy as np
from PIL import Image
import z80core
from z80core import Z80

LINE = 256
FRAME = 312 * LINE
HW = [(128,128,128),(128,128,128),(0,255,128),(255,255,128),(0,0,128),(255,0,128),(0,128,128),(255,128,128),
      (255,0,128),(255,255,128),(255,255,0),(255,255,255),(255,0,0),(255,0,255),(255,128,0),(255,128,255),
      (0,0,128),(0,255,128),(0,255,0),(0,255,255),(0,0,0),(0,0,255),(0,128,0),(0,128,255),
      (128,0,128),(128,255,128),(128,255,0),(128,255,255),(128,0,0),(128,0,255),(128,128,0),(128,128,255)]
DISP0 = 72          # linea del cuadro (desde VSYNC) donde empieza la imagen visible


class CPC:
    def __init__(s):
        s.ram = bytearray(65536)
        s.pen = 0; s.ink = [0x14] * 17; s.mode = 1; s.romcfg = 0x0C
        s.crtc = [63, 40, 46, 0x8E, 38, 0, 25, 30, 0, 7, 0, 0, 0x30, 0, 0, 0, 0, 0]
        s.creg = 0
        s.ppi_a = 0xFF; s.ppi_c = 0; s.psg = [0] * 16; s.preg = 0
        s.keys = [0xFF] * 10
        s.galog = []            # (ciclo, tipo, a, b) cambios del gate array durante el cuadro
        s.wlog = None
    def slot(s, page): return 0
    def rd(s, a): return s.ram[a & 0xFFFF]
    def wr(s, a, v):
        a &= 0xFFFF
        if s.wlog is not None: s.wlog(a, v)
        s.ram[a] = v & 255


class CPU(Z80):
    def __init__(s, m):
        Z80.__init__(s, m)
        s.next_int = 0; s.line = 0; s.fstart = 0; s.intreq = False; s.gacnt = 0
        s.frames = 0; s.on_frame = None; s.snap = None; s.portlog = None
    # ---- E/S ----
    def inp(s, p):
        m = s.m; hi = p >> 8
        if not hi & 0x08:          # PPI
            r = hi & 3
            if r == 0:
                if (m.ppi_c >> 6) == 1:
                    if m.preg == 14: return m.keys[m.ppi_c & 15] if (m.ppi_c & 15) < 10 else 0xFF
                    return m.psg[m.preg]
                return 0xFF
            if r == 1:
                ln = (s.cyc - s.fstart) // LINE
                return 0x1E | (1 if ln < 8 else 0)
            if r == 2: return m.ppi_c
        return 0xFF
    def outp(s, p, v):
        m = s.m; hi = p >> 8
        if s.portlog is not None: s.portlog(s, p, v)
        if (hi & 0xC0) == 0x40:    # gate array
            t = v >> 6
            if t == 0: m.pen = 16 if v & 0x10 else v & 15
            elif t == 1:
                m.ink[m.pen] = v & 31; m.galog.append((s.cyc - s.fstart, 'ink', m.pen, v & 31))
            elif t == 2:
                m.mode = v & 3; m.romcfg = v; m.galog.append((s.cyc - s.fstart, 'mode', v & 3, 0))
                if v & 0x10: s.gacnt = 0; s.intreq = False
        if not hi & 0x40:          # CRTC
            r = hi & 3
            if r == 0: m.creg = v & 31
            elif r == 1 and m.creg < 18: m.crtc[m.creg] = v
        if not hi & 0x08:          # PPI
            r = hi & 3
            if r == 0: m.ppi_a = v
            elif r == 2:
                m.ppi_c = v; s._psg()
            elif r == 3:
                if not v & 0x80:
                    bit = (v >> 1) & 7
                    m.ppi_c = (m.ppi_c | (1 << bit)) if v & 1 else (m.ppi_c & ~(1 << bit)); s._psg()
    def _psg(s):
        m = s.m; f = m.ppi_c >> 6
        if f == 3: m.preg = m.ppi_a & 15
        elif f == 2: m.psg[m.preg] = m.ppi_a
    # ---- ejecucion ----
    def step(s):
        m = s.m
        while s.cyc >= s.next_int:      # nueva linea
            s.next_int += LINE; s.line += 1
            if s.line >= 312:
                s.line = 0
                if s.snap: s.snap(s)
                m.galog = []; s.fstart = s.next_int - LINE; s.frames += 1
                if s.on_frame: s.on_frame(s)
            s.gacnt += 1
            if s.line == 2:              # 2 HSYNC tras el VSYNC
                if s.gacnt >= 32: s.intreq = True
                s.gacnt = 0
            elif s.gacnt >= 52:
                s.gacnt = 0; s.intreq = True
        if s.intreq and s.iff:
            s.intreq = False; s.gacnt &= 31; s.iff = 0; s.halt = False
            s.push(s.PC)
            if s.im == 2:
                v = (s.I << 8) | 0xFF; s.PC = m.rd(v) | m.rd(v + 1) << 8
            else: s.PC = 0x38
            s.cyc += 13
        pc = s.PC
        h = s.hooks.get(pc)
        if h is not None and h(s): return
        if s.halt: s.cyc += 4; return
        s._ins()


def render(m, galog=None, inks=None, mode=None):
    """imagen 2x (pixeles de modo 1 = 2 columnas en modo 2) de 640x200 en coordenadas de modo 2"""
    c = m.crtc
    base = (c[12] << 8) | c[13]
    w = c[1] * 2; rows = c[6]; ra = c[9] + 1
    H = rows * ra
    img = np.zeros((H, w * 8, 3), np.uint8)
    ink = list(inks or m.ink); md = m.mode if mode is None else mode
    ev = sorted(galog or [], key=lambda e: e[0]); ei = 0
    pal = None
    d0 = (c[4] + 1 - c[7]) * (c[9] + 1) + c[5]
    for y in range(H):
        cyc = (d0 + y) * LINE
        while ei < len(ev) and ev[ei][0] <= cyc:
            _, t, a, b = ev[ei]
            if t == 'ink': ink[a] = b
            else: md = a
            ei += 1
        row, r = divmod(y, ra)
        ma = base + row * c[1]
        addr0 = ((ma & 0x3000) << 2) | ((r & 7) << 11)
        pal = np.array([HW[k] for k in ink[:16]], np.uint8)
        line = []
        for i in range(w):
            mai = (ma + i // 2) & 0x3FF
            a = addr0 | (((mai << 1) | (i & 1)) & 0x7FF)
            line.append(m.ram[a])
        b = np.array(line, np.uint8)
        if md == 1:
            px = np.zeros((w, 4), np.uint8)
            for k in range(4):
                px[:, k] = ((b >> (7 - k)) & 1) | (((b >> (3 - k)) & 1) << 1)
            px = np.repeat(px.reshape(-1), 2)
        elif md == 0:
            px = np.zeros((w, 2), np.uint8)
            for k in range(2):
                px[:, k] = ((b >> (7 - k)) & 1) | (((b >> (3 - k)) & 1) << 1) | (((b >> (5 - k)) & 1) << 2) | (((b >> (1 - k)) & 1) << 3)
            px = np.repeat(px.reshape(-1), 4)
        else:
            px = np.zeros((w, 8), np.uint8)
            for k in range(8): px[:, k] = (b >> (7 - k)) & 1
            px = px.reshape(-1)
        img[y] = pal[px]
    return Image.fromarray(img)


def boot(files):
    """files: dict nombre->bytes (sin cabecera). Reproduce CARGA (BASKET.BAS + CARGA.BIN) sin firmware."""
    m = CPC(); c = CPU(m)
    r = m.ram
    carga = files['CARGA.BIN']; r[0x19A:0x19A + len(carga)] = carga
    cb = files['CB.BIN']; r[0x226:0x226 + len(cb)] = cb
    an = files['ANIPAN.BIN']; r[0xBFCC:0xBFCC + len(an)] = an
    # inks a 0 (rutina 0201h) y modo 1
    r[0x38] = 0xC3
    m.mode = 1; m.ink = [0x14] * 17
    c.SP = 0xBFCC; c.PC = 0x1D1; c.iff = 0; c.im = 1   # 'di' tras cargar
    return m, c


def load_disk(path):
    import cpm
    f, _, _ = cpm.load(path)
    return {n: d[128:128 + (d[0x18] | d[0x19] << 8)] for n, (d, _) in f.items() if n.endswith(('.BIN', '.BAS'))}
