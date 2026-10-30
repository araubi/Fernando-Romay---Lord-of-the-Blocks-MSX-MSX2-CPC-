import build, frames, fsheet, zoomp
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.shot('/tmp/claude-0/sel1.png')
s.key('2'); s.run(150); s.shot('/tmp/claude-0/sel2.png')
C=frames.cpc_frames(bytes(s.m.ram),n=75)
fsheet.sheet(C,None,list(range(48,62))+[10,11,22,23,34,35,46,47],'/tmp/claude-0/selfr.png',sc=3)
for k in range(3):
    s.run(40); zoomp.players(s,'/tmp/claude-0/sz%d.png'%k)
s.save('/tmp/claude-0/cpc_romay.pkl')
