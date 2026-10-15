import build, random, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
mode=sys.argv[1]
if 'L' in mode:
    for k in range(3): s.key('3'); s.run(30)
s.key('1'); s.run(60); s.key('2' if 'R' in mode else '1'); s.run(100)
rnd=random.Random(int(sys.argv[2])); f=s.c.frames+10
while f<s.c.frames+30000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
z=[]
s.c.hooks[0x249B]=lambda cpu:(z.append(cpu.frames),False)[1]
zs=[]; n=0; end=s.c.frames+30000
while s.c.frames<end:
    s.c.step()
    if z and n<len(z) and (n==0 or z[-1]-zs[-1]>300):
        zs.append(z[-1])
        n=len(z); print('zoom at',z[-1],flush=True)
        for k in range(4):
            e2=s.c.frames+15
            while s.c.frames<e2: s.c.step()
            s.img().save('/tmp/claude-0/zoom_%s_%d_%d.png'%(mode,n,k))
        if len(zs)>=2: break
print('zooms',z)
