import build
from sess import Sess
im=build.make(); print(im.placed)
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800); s.key('1'); s.run(150)
c=s.c; m=s.m
def pos(): return (m.ram[0x1131],m.ram[0x1132]),(m.ram[0x114B],m.ram[0x114C])
print('start',pos())
for k in ['up','down','left','right']:
    s.key(k,dur=40); s.run(45); print(k,pos())
s.shot('../out/t2.png')
