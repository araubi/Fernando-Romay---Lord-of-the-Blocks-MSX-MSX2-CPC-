import build, random
from sess import Sess
from PIL import Image
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(3): s.key('3'); s.run(30)
s.key('1'); s.run(60); s.key('1'); s.run(150)
got={'R':[], 'L':[]}
prev=s.m.ram[0x114C]
for t in range(600):
    s.run(3); r=s.m.ram; h=r[0x114C]; l=r[0x114B]
    d='R' if h>prev else ('L' if h<prev else None); prev=h
    if d and len(got[d])<3 and abs(h-r[0x1132])>20:
        img=s.img(); x=(32+2*h)*2; y=24+l
        got[d].append(img.crop((x-20,y-48,x+60,y-13)).resize((480,210),Image.NEAREST))
    if all(len(v)>=3 for v in got.values()): break
W=Image.new('RGB',(480*3,210*2),(60,60,60))
for j,d in enumerate('RL'):
    for i,c in enumerate(got[d]): W.paste(c,(i*480,j*210))
W.save('../out/jrun.png'); print({k:len(v) for k,v in got.items()})
