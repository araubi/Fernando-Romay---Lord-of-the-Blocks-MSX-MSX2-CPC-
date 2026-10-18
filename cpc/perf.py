import sys, random, statistics, build
from sess import Sess
which=sys.argv[1]; N=int(sys.argv[2]); seed=int(sys.argv[3])
files=None if which=='orig' else build.make().files()
s=Sess(files=files) if files else Sess()
s.run(700); s.key('space'); s.run(800); s.key('1'); s.run(60)
if which!='orig': s.key('1'); s.run(60); s.key('1'); s.run(60)
rnd=random.Random(seed); f=s.c.frames+10
while f<s.c.frames+N:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60)
    s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
    s.key(rnd.choice(['j0u','j0d','j0l','j0r','j0f1']),at=f,dur=rnd.randint(5,40))
loop=[]; zoom=[]
c=s.c
c.hooks[0x02A3]=lambda cpu:(loop.append(cpu.cyc),False)[1]
c.hooks[0x249B]=lambda cpu:(zoom.append(cpu.cyc),False)[1]
s.run(N)
F=312*256
g=[(b-a)/F for a,b in zip(loop,loop[1:]) if (b-a)/F<12]
z=[(b-a)/F for a,b in zip(zoom,zoom[1:]) if (b-a)/F<12]
print(which,seed,'juego: %d vueltas, media %.3f (mediana %.2f, p90 %.2f)'%(len(g),statistics.mean(g),statistics.median(g),sorted(g)[int(len(g)*.9)]),
      'repeticion: %d, media %.3f'%(len(z),statistics.mean(z)) if z else 'sin repeticion', flush=True)
