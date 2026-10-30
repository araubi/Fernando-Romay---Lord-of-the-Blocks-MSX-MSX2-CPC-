import scrmap
import sys, random, collections
import build
from sess import Sess
mode=sys.argv[1]; N=int(sys.argv[2]); seed=int(sys.argv[3]); tag=sys.argv[4]
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
if 'L' in mode:
    for k in range(3): s.key('3'); s.run(30)
if '2' in mode: s.key('2'); s.run(100); s.key('1'); s.run(60)
else:
    s.key('1'); s.run(60); s.key('2' if 'R' in mode else '1'); s.run(100); s.key('1'); s.run(60)
rnd=random.Random(seed); f=s.c.frames+10
keys1=['up','down','left','right','left','right','space','space']
keys2=['w','s','a','d','shift']
while f<s.c.frames+N:
    k=rnd.choice(keys1); d=rnd.randint(5,60); s.key(k,at=f,dur=d)
    if '2' in mode: s.key(rnd.choice(keys2),at=f+3,dur=rnd.randint(5,60))
    f+=d+rnd.randint(1,8)
m=s.m; c=s.c; r=m.ram
st=collections.Counter(); badpc=[0]
def chk(cpu):
    bad=0
    for row in range(104):
        a=r[0x8118+2*row]|r[0x8119+2*row]<<8
        if r[a:a+64]!=r[0xA568+64*row:0xA568+64*row+64]: bad+=1
    st['ok' if bad==0 else 'bad']+=1
    if r[0x7394]: st['full']+=1
    if bad and st['bad']<3: s.img().save('../out/pb_%s_%d.png'%(tag,st['bad'])); print('bad',cpu.frames,bad,flush=True)
    return False
c.hooks[0x02D9]=chk
BGTAB=im.bgtab
def chk2(cpu):
    if r[0x7394]==0:
        for row in range(104):
            a=r[BGTAB+2*row]|r[BGTAB+2*row+1]<<8
            if r[a:a+64]!=r[0xA568+64*row:0xA568+64*row+64]: st['bgerr']+=1; break
    return False
c.hooks[0x02A6]=chk2
end=c.frames+N; last=-1
while c.frames<end:
    c.step()
    if c.PC<0x100 or not scrmap.code_ok(c.PC): badpc[0]+=1
    if c.frames%3000==0 and c.frames!=last:
        last=c.frames; s.shot('../out/p2_%s_%d.png'%(tag,c.frames))
print(tag, dict(st), 'badpc', badpc[0], flush=True)
