# escrituras en pantalla fuera de las columnas 8-71 (los 256 px centrales) o en los huecos
import build, random, collections, pickle, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files())
W=collections.defaultdict(collections.Counter)
phase=['boot']
m=s.m; c=s.c
def wl(a,v):
    if a>=0xC000:
        o=(a-0xC000)&0x7FF
        if o>=2000: W[phase[0]][(hex(c.PC),'gap')]+=1
        else:
            col=o%80
            if col<8 or col>71: W[phase[0]][(hex(c.PC),'col%d'%col if v!=m.ram[a] else 'same')]+=1
m.wlog=wl
def P(n,f): phase[0]=n; s.run(f); print(n,c.frames,flush=True)
P('intro',700); s.key('space'); P('menu',800)
s.key('4'); P('opt4',300); s.key('esc'); P('opt4b',200)
s.key('1'); P('charsel',60); s.key('1'); P('posmenu',100); s.key('1'); P('kick',300)
rnd=random.Random(3); f=c.frames+10
while f<c.frames+12000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
P('match',12000)
s.m.ram[0x110B:0x110E]=b'003'; P('half',2500); s.key('space'); P('half2',800)
s.m.ram[0x110B:0x110E]=b'003'; P('end',3000); s.key('space'); P('end2',3000)
for n in W: print('W',n,sorted(W[n].items())[:60])
