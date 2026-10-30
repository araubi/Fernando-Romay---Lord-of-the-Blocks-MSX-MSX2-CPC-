import build, random
from sess import Sess
from PIL import Image
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(5); f=s.c.frames+10
while f<s.c.frames+30000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
z=[]
s.c.hooks[0x2417]=lambda cpu:(z.append(cpu.frames),False)[1]
while not z: s.c.step()
shots=[]
for k in range(48):
    s.run(1); shots.append(s.img())
W=Image.new('RGB',(640*4,200*12))
for i,c in enumerate(shots): W.paste(c,((i%4)*640,(i//4)*200))
W.resize((1280,1200)).save('../out/trans.png')
