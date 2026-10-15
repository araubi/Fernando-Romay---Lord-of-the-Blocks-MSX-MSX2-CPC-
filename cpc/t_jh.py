import build, random
from sess import Sess
from PIL import Image
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(3): s.key('3'); s.run(30)
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(3); f=s.c.frames+10
while f<s.c.frames+6000:
    k=rnd.choice(['up','down','left','right','space']); d=rnd.randint(5,40); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
crops=[]
for t in range(60):
    s.run(17); r=s.m.ram; img=s.img()
    crops.append(img.crop((40,40,600,130)))
for p in range(3):
    W=Image.new('RGB',(560*2,90*2*5))
    for i,c in enumerate(crops[p*10:p*10+10]): W.paste(c.resize((1120,180),Image.NEAREST) if False else c,((i%2)*560,(i//2)*90))
    W=W.crop((0,0,1120,450)).resize((2240,900),Image.NEAREST); W.save('/tmp/claude-0/jh_%d.png'%p)
