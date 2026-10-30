import build, random
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(5); f=s.c.frames+10
while f<s.c.frames+3000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
ev=[]
for a,n in [(0x2417,'replay'),(0x7588,'black'),(0x7581,'pal'),(L['MLOOP'],'mloop'),(0x249B,'zoomdraw')]:
    s.c.hooks[a]=(lambda n: lambda cpu:(ev.append((cpu.frames,n,s.m.ram[L['MATCH']])),False)[1])(n)
s.run(1300)
last=None
for e in ev:
    if e[1]!=last or e[1] not in ('mloop','zoomdraw'): print(e)
    last=e[1]
