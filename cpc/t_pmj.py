import sys
import build
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(int(sys.argv[3])): s.key('3'); s.run(30)
import sys; s.key(sys.argv[1]); s.run(60); s.key(sys.argv[2]); s.run(150)
s.shot('/tmp/claude-0/pmj.png')
