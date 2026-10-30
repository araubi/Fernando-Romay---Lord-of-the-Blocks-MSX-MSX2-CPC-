"""Ejecuta la ROM SCREEN 5 en el emulador con un guion de teclas y saca capturas."""
import os, sys, random, collections
os.environ.setdefault('MSX_TIMED', '1'); os.environ.setdefault('MSX_FRAME', '71364')
import msx
from s5emu import boot5
from session import press, KEY
KEY.update({'D': (3, 1), 'F': (3, 3), 'Q': (4, 6), 'Z': (5, 7), 'ESC': (7, 2)})
def script(frames, seed, start=(450, 650, 800)):
    rnd = random.Random(seed)
    a, b, c = start
    sc = press('SPACE', a) + press('1', b) + press('1', c)
    f = c + 60
    while f < frames:
        k = rnd.choice(['RIGHT', 'LEFT', 'UP', 'DOWN', 'RIGHT', 'LEFT', 'SPACE', 'SPACE'])
        d = rnd.randint(5, 70); sc += [(f, k, True), (f + d, k, False)]; f += d + rnd.randint(1, 8)
    return sc
def run(rom, frames, sc=None, shots=(), seed=3, hooks=None, every=None, onframe=None):
    m, c = boot5(rom); m.slot = lambda p: 0
    ev = sorted(sc if sc is not None else script(frames, seed)); ims = {}
    def onf(cpu):
        while ev and ev[0][0] <= cpu.frames:
            _, k, dn = ev.pop(0); r, b = KEY[k]; m.keys[r] = (m.keys[r] & ~(1 << b)) if dn else (m.keys[r] | (1 << b))
        if cpu.frames in shots or (every and cpu.frames % every == 0): ims[cpu.frames] = m.vdp.render()
        if onframe: onframe(cpu)
    c.on_frame = onf
    for a, h in (hooks or {}).items(): c.hooks[a] = h
    while c.frames < frames: c.step()
    return m, c, ims
def sheet(ims, cols=6, scale=1):
    from PIL import Image
    ks = sorted(ims); W = 256 * scale; H = 192 * scale
    S = Image.new('RGB', (W * cols, H * ((len(ks) + cols - 1) // cols)))
    for i, k in enumerate(ks):
        S.paste(ims[k].resize((W, H)), ((i % cols) * W, (i // cols) * H))
    return S
if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read(); N = int(sys.argv[2])
    m, c, ims = run(rom, N, every=int(sys.argv[3]) if len(sys.argv) > 3 else 200)
    sheet(ims).save('../out/s5sheet.png')
    print('PC %04X frames %d' % (c.PC, c.frames))
