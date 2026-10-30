# inventario: que codigo escribe/lee la memoria de pantalla en cada fase
import build, random, collections, pickle, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files())
W=collections.defaultdict(collections.Counter); R=collections.defaultdict(collections.Counter)
phase=['boot']
m=s.m; ram=m.ram; c=s.c
def wl(a,v):
    if a>=0xC000: W[phase[0]][c.PC]+=1
m.wlog=wl
orig_rd=m.rd
def rd(a):
    a&=0xFFFF
    if a>=0xC000 and a!=c.PC: R[phase[0]][c.PC]+=1
    return ram[a]
m.rd=rd
def P(n,f): phase[0]=n; s.run(f); print(n,c.frames,flush=True)
P('intro',700); s.key('space'); P('menu',800)
s.key('4'); P('opt4',300); s.key('esc'); P('opt4b',200)
s.key('1'); P('charsel',60); s.key('1'); P('posmenu',100); s.key('1'); P('kick',300)
rnd=random.Random(3); f=c.frames+10
while f<c.frames+12000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
P('match',12000)
ram[0x110B:0x110E]=b'003'; P('half',2500); s.key('space'); P('half2',800)
ram[0x110B:0x110E]=b'003'; P('end',3000); s.key('space'); P('end2',3000)
s.shot('/tmp/claude-0/inv_last.png')
pickle.dump((dict(W),dict(R)),open('/tmp/claude-0/inv.pkl','wb'))
for n in W: print('W',n,sorted((hex(k),v) for k,v in W[n].items()))
for n in R: print('R',n,sorted((hex(k),v) for k,v in R[n].items()))
