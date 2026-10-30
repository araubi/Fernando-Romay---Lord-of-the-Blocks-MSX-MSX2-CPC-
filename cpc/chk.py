"""recorrido largo: en la build vieja, escrituras fuera de las columnas 8-71; en la nueva, escrituras en
las zonas libres de la pantalla (filas 0 y 23-24 de cada bloque) desde el menu, salvo variables de lo colocado"""
import sys, os, random, collections
D = sys.argv[1]; mode = sys.argv[2]; N = int(sys.argv[3])
sys.path.insert(0, D); os.chdir(D)
import build
from sess import Sess
im = build.make(); s = Sess(files=im.files()); m = s.m; c = s.c
PL = getattr(im, 'placed', [])
NEW = os.path.exists(os.path.join(D, 'scrmap.py'))
W = collections.defaultdict(collections.Counter); phase = ['boot']; armed = [False]
def wl(a, v):
    if a < 0xC000: return
    o = (a - 0xC000) & 0x7FF
    if NEW:
        if armed[0] and (o >= 0x5C0 or o < 0x40) and not any(p0 <= a < p0 + n for _, p0, n in PL): W[phase[0]][(hex(c.PC), hex(a))] += 1
    else:
        if o >= 2000: W[phase[0]][(hex(c.PC), 'gap')] += 1
        elif not (8 <= o % 80 <= 71) and v != m.ram[a]: W[phase[0]][(hex(c.PC), 'col%d' % (o % 80))] += 1
m.wlog = wl
def P(n, f): phase[0] = n; s.run(f); print(n, c.frames, flush=True)
P('intro', 700); s.key('space'); P('menu', 800); armed[0] = True
if 'L' in mode:
    for k in range(3): s.key('3'); s.run(30)
if '2' in mode: s.key('2'); P('pos', 100); s.key('2'); P('kick', 300)
else:
    s.key('1'); P('charsel', 60); s.key('2' if 'R' in mode else '1'); P('pos', 100); s.key('3'); P('kick', 300)
rnd = random.Random(int(sys.argv[4])); f = c.frames + 10
while f < c.frames + N:
    k = rnd.choice(['up', 'down', 'left', 'right', 'left', 'right', 'space', 'space']); d = rnd.randint(5, 60); s.key(k, at=f, dur=d)
    if '2' in mode: s.key(rnd.choice(['w', 's', 'a', 'd', 'shift']), at=f + 3, dur=rnd.randint(5, 60))
    f += d + rnd.randint(1, 8)
z = []
c.hooks[0x249B] = lambda cpu: (z.append(cpu.frames), False)[1]
P('match', N)
print('zooms', len(z))
m.ram[0x110B:0x110E] = b'003'; P('half', 2500); s.key('space'); P('half2', 800)
m.ram[0x110B:0x110E] = b'003'; P('end', 3000); s.key('space'); P('end2', 3000)
s.shot('../out/chk_%s_%s.png' % ('new' if NEW else 'old', mode))
for n in W: print('W', n, sorted(W[n].items(), key=str)[:80])
print('FIN')
