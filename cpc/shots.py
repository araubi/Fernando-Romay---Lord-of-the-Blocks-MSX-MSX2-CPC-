import build
from sess import Sess
from PIL import Image
im=build.make()
open('../out/Fernando_Romay_Lord_of_the_Blocks_CPC.dsk','wb').write(im.dsk())
s=Sess(files=im.files()); s.run(300); a=s.img()
s.run(400); s.key('space'); s.run(800); b=s.img()
s.key('1'); s.run(60); c=s.img()
s.key('1'); s.run(400); d=s.img()
s2=Sess(files=im.files()); s2.run(700); s2.key('space'); s2.run(800)
for k in range(3): s2.key('3'); s2.run(30)
s2.key('1'); s2.run(60); s2.key('2'); s2.run(500); e=s2.img()
ims=[a,b,c,d,e]
W=Image.new('RGB',(1280,1200),(30,30,30))
for i,x in enumerate(ims): W.paste(x.resize((640,400)),((i%2)*640,(i//2)*400))
W.save('../out/CPC_avance1.png')
