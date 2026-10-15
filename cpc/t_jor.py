import build, zoomp
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(3): s.key('3'); s.run(30)
s.shot('/tmp/claude-0/jm.png')
s.key('1'); s.run(60); s.key('1'); s.run(200)
s.img().resize((1280,400)).save('/tmp/claude-0/jg.png')
for k in range(3):
    s.run(50); zoomp.players(s,'/tmp/claude-0/jz%d.png'%k)
s.save('/tmp/claude-0/cpc_jordan.pkl')
