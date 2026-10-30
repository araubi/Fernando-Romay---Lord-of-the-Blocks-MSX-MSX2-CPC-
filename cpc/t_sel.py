import build, frames, fsheet, zoomp
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.shot('../out/sel1.png')
s.key('2'); s.run(150); s.shot('../out/sel2.png')
C=frames.cpc_frames(bytes(s.m.ram),n=75)
fsheet.sheet(C,None,list(range(48,62))+[10,11,22,23,34,35,46,47],'../out/selfr.png',sc=3)
for k in range(3):
    s.run(40); zoomp.players(s,'../out/sz%d.png'%k)
s.save('../out/cpc_romay.pkl')
