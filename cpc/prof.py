import sys, random, collections, build
from sess import Sess
which=sys.argv[1]
im=build.make()
s=Sess(files=None if which=='orig' else im.files())
s.run(700); s.key('space'); s.run(800); s.key('1'); s.run(60)
if which!='orig': s.key('1'); s.run(60)
rnd=random.Random(1); f=s.c.frames+10
while f<s.c.frames+3000:
    k=rnd.choice(['up','down','left','right','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
c=s.c; hist=collections.Counter(); end=c.frames+3000
while c.frames<end:
    pc=c.PC; c0=c.cyc; c.step(); hist[pc>>6]+=c.cyc-c0
tot=sum(hist.values())
for k,v in hist.most_common(25): print('%04X %5.2f%%'%(k<<6, 100*v/tot))
