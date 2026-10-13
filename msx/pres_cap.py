"""Captura la presentacion en G2: imagen estatica y fotogramas animados (indices de color MSX1)."""
import sys, pickle, numpy as np
from s5_run import *
def g2idx(v):
    r = v.reg; vr = v.vram
    nt = (r[2] & 0x7F) << 10; ct = ((r[10] & 7) << 14) | ((r[3] & 0x80) << 6); pt = (r[4] & 0x3C) << 11
    a = np.zeros((192, 256), np.uint8)
    for y in range(192):
        for tx in range(32):
            ch = vr[nt + (y >> 3) * 32 + tx] + (y >> 6) * 256
            p = vr[pt + ch * 8 + (y & 7)]; c = vr[ct + ch * 8 + (y & 7)]
            for k in range(8): a[y, tx * 8 + k] = (c >> 4) if p & (0x80 >> k) else (c & 15)
    return a
def capture(rom):
    out = {'calls': []}; st = {}
    def enter(cpu):
        if 'static' not in out: out['static'] = g2idx(cpu.m.vdp)
    def after(cpu):
        m = cpu.m; y = m.ram[0xD098]; col = m.ram[0xD099]; h = m.ram[0xD0A0]; w = m.ram[0xD0A2]
        src = m.ram[0xD09A] | m.ram[0xD09B] << 8
        a = g2idx(cpu.m.vdp)
        out['calls'].append((src, y, col, h, w, a[y:y + h, col * 8:col * 8 + w * 8].copy()))
    m, c, ims = run(rom, 420, sc=[], hooks={0xCC76: enter, 0xCCE4: after})
    return out
if __name__ == '__main__':
    o = capture(open('s5.rom', 'rb').read())
    srcs = {}
    for s, y, col, h, w, a in o['calls']: srcs.setdefault(s, (y, col, h, w, a))
    print(len(o['calls']), {('%04X' % k): v[:4] for k, v in srcs.items()})
    pickle.dump({'static': o['static'], 'frames': srcs}, open('pres_cap.pkl', 'wb'))

def shadow(v):
    """pantalla G2 de la sombra (banco 7) aunque se muestre G4"""
    vr = v.vram; a = np.zeros((192, 256), np.uint8)
    for y in range(192):
        for tx in range(32):
            ch = vr[0x1D800 + (y >> 3) * 32 + tx] + (y >> 6) * 256
            p = vr[0x1C000 + ch * 8 + (y & 7)]; c = vr[0x1E000 + ch * 8 + (y & 7)]
            for k in range(8): a[y, tx * 8 + k] = (c >> 4) if p & (0x80 >> k) else (c & 15)
    return a
