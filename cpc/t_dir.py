import build, random
from sess import Sess
from PIL import Image
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800); s.shot('/tmp/claude-0/d_menu.png')
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(5); f=s.c.frames+10
while f<s.c.frames+6000:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
shots=[]
for k in range(12):
    s.run(37); shots.append(s.img())
W=Image.new('RGB',(640*2,200*6))
for i,c in enumerate(shots): W.paste(c,((i%2)*640,(i//2)*200))
W.save('/tmp/claude-0/dir.png'); print('PC %04X'%s.c.PC)
s.save('/tmp/claude-0/cpc_dir.pkl')
