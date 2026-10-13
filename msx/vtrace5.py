"""Traza de escrituras VRAM en la sombra G2 (banco 7) con la pila de llamadas, ROM S5."""
import sys, collections, pickle
from s5_run import *
def trace(rom, frames, sc, depth=3, f0=0):
    agg = collections.defaultdict(lambda: [0, 10**9, 0, 99, -1, 99, -1])
    st = {}
    def onf(cpu): pass
    m, c = None, None
    def hook_log(mm, cc):
        def lg(a, v):
            if cc.frames < f0 or a < 0x1C000: return
            if a < 0x1D800: cell = (a - 0x1C000) >> 3; kind = 'P'
            elif 0x1E000 <= a < 0x1F800: cell = (a - 0x1E000) >> 3; kind = 'C'
            else: return
            sp = cc.SP; stk = []
            for i in range(24):
                w = mm.ram[(sp + 2 * i) & 0xFFFF] | mm.ram[(sp + 2 * i + 1) & 0xFFFF] << 8
                if w >= 3 and mm.ram[w - 3] in (0xCD, 0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC):
                    stk.append(w - 3)
                    if len(stk) == depth: break
            stk = tuple(stk)
            k = (stk, kind); e = agg[k]
            r, col = cell >> 5, cell & 31
            e[0] += 1; e[1] = min(e[1], cc.frames); e[2] = max(e[2], cc.frames)
            e[3] = min(e[3], r); e[4] = max(e[4], r); e[5] = min(e[5], col); e[6] = max(e[6], col)
        mm.vdp.log = lg
    import s5emu
    rom_ = rom
    m, c = boot5(rom_); m.slot = lambda p: 0
    hook_log(m, c)
    ev = sorted(sc)
    def onf(cpu):
        while ev and ev[0][0] <= cpu.frames:
            _, k, dn = ev.pop(0); r, b = KEY[k]; m.keys[r] = (m.keys[r] & ~(1 << b)) if dn else (m.keys[r] | (1 << b))
    c.on_frame = onf
    while c.frames < frames: c.step()
    return agg
def show(agg):
    for (stk, kind), (n, a, b, r0, r1, c0, c1) in sorted(agg.items(), key=lambda kv: kv[1][1]):
        print('%s %s n=%-6d f%5d-%5d rows %2d-%2d cols %2d-%2d' % (' '.join('%04X' % s for s in stk), kind, n, a, b, r0, r1, c0, c1))
if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read(); N = int(sys.argv[2])
    sc = press('SPACE', 450)
    show(trace(rom, N, sc))
