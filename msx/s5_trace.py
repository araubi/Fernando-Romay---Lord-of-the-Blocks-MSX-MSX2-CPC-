"""Traza de escrituras en VRAM por sitio (PC) y zona, imagen MSX1 sin sprite_patch."""
import collections, random, sys, pickle
from session import *
import mk
KEY.update({'D':(3,1),'F':(3,3),'Q':(4,6),'Z':(5,7)})
def region(a):
    if a < 0x1800: return 'pat%d' % (a // 0x800)
    if a < 0x1B00: return 'name'
    if a < 0x1B80: return 'sat'
    if a < 0x2000: return 'x1B80'
    if a < 0x3800: return 'col%d' % ((a - 0x2000) // 0x800)
    return 'spat'
def script(frames, seed):
    rnd = random.Random(seed)
    sc = press('SPACE', 120) + press('1', 340) + press('1', 420)
    f = 470
    while f < frames:
        k = rnd.choice(['RIGHT', 'LEFT', 'UP', 'DOWN', 'RIGHT', 'LEFT', 'SPACE', 'SPACE'])
        d = rnd.randint(5, 70); sc += [(f, k, True), (f + d, k, False)]; f += d + rnd.randint(1, 8)
    return sc
def trace(img, frames=6000, seed=3, shots=()):
    m, c = load_from_cas(img); ev = sorted(script(frames, seed))
    agg = collections.defaultdict(lambda: [0, 10**9, 0, 0xFFFF, 0])
    ims = {}
    def onf(cpu):
        while ev and ev[0][0] <= cpu.frames:
            _, k, dn = ev.pop(0); r, b = KEY[k]; m.keys[r] = (m.keys[r] & ~(1 << b)) if dn else (m.keys[r] | (1 << b))
        if cpu.frames in shots: ims[cpu.frames] = m.vdp.render()
    c.on_frame = onf
    def lg(a, v):
        k = (m.vdp.pc, region(a)); e = agg[k]
        e[0] += 1; e[1] = min(e[1], c.frames); e[2] = max(e[2], c.frames); e[3] = min(e[3], a); e[4] = max(e[4], a)
    m.vdp.log = lg
    while c.frames < frames: c.step()
    return agg, ims, m, c
if __name__ == '__main__':
    img = mk.make(skip=('sprite_patch',))
    open('base_nospr.cas', 'wb').write(img)
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    agg, ims, m, c = trace(img, N, shots=tuple(range(500, N, 500)))
    for (pc, reg), (n, f0, f1, a0, a1) in sorted(agg.items()):
        print('%04X %-6s n=%-7d f%5d-%5d  %04X-%04X' % (pc, reg, n, f0, f1, a0, a1))
    for f, im in ims.items(): im.save('/tmp/claude-0/s5t_%d.png' % f)
    pickle.dump(dict(agg), open('/tmp/claude-0/s5trace.pkl', 'wb'))
