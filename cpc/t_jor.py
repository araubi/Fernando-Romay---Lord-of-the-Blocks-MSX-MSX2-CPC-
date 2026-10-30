import build, zoomp
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(3): s.key('3'); s.run(30)
s.shot('../out/jm.png')
s.key('1'); s.run(60); s.key('1'); s.run(200)
s.img().resize((1280,400)).save('../out/jg.png')
for k in range(3):
    s.run(50); zoomp.players(s,'../out/jz%d.png'%k)
s.save('../out/cpc_jordan.pkl')
