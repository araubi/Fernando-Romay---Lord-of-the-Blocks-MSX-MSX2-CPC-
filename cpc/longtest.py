import sys, random, time, pickle
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
bad=0; t=time.time(); end=s.c.frames+N; last=-1
c=s.c
while c.frames<end:
    c.step()
    if c.PC>=0xC000 or c.PC<0x100: bad+=1
    if c.frames%2500==0 and c.frames!=last:
        last=c.frames; s.shot('/tmp/claude-0/lt_%s_%d.png'%(tag,c.frames)); print(c.frames,'bad',bad,'%.0f'%(time.time()-t),flush=True)
s.save('/tmp/claude-0/lt_%s_end.pkl'%tag)
print('done bad',bad)
