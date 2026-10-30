import build, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key(sys.argv[1] if len(sys.argv)>1 else '1'); s.run(100); s.key('1'); s.run(300)
r=s.m.ram; r[0x110B:0x110E]=b'003'
ev=[]
s.c.hooks[L['STAT2']]=lambda cpu:(ev.append(cpu.frames),False)[1]
for k in range(16):
    s.run(150); s.shot('../out/half_%02d.png'%k)
print(ev, hex(s.c.PC))
