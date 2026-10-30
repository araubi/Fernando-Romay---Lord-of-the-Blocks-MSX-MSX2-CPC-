import build, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100); s.key('1'); s.run(300)
r=s.m.ram; r[0x110B:0x110E]=b'003'
s.run(1500); s.key('space'); s.run(600); s.shot('../out/end_0.png')
r[0x110B:0x110E]=b'003'
ev=[]
for n in ('STAT2','MENU2'): s.c.hooks[L[n]]=(lambda n: lambda cpu:(ev.append((n,cpu.frames)),False)[1])(n)
for k in range(1,40):
    s.run(300); s.shot('../out/end_%d.png'%k)
    if k==6: s.key('space')
print(ev, hex(s.c.PC), s.m.crtc[7], hex(r[0x8118]))
