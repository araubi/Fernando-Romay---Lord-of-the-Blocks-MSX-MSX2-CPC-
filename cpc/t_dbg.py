import build, random
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(5); f=s.c.frames+10
while f<s.c.frames+30000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
z=[]
s.c.hooks[0x2417]=lambda cpu:(z.append(cpu.frames),False)[1]
while not z: s.c.step()
out=[]
for k in range(48):
    s.run(1); out.append((s.m.ram[L['MATCH']], s.m.ram[L['ZCNT']], s.m.ram[L['RCNT']]))
print(out)
