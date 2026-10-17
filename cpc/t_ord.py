from sess import Sess
import build
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800); s.key('1'); s.run(60); s.key('1'); s.run(300)
c=s.c; m=s.m; log=[]
def mk(name):
    def h(cpu):
        sp=cpu.SP; log.append((name, hex(m.ram[sp]|m.ram[sp+1]<<8)))
        return False
    return h
for a,n in [(0x02A3,'loop'),(0x02D0,'draw10A9'),(0x83F8,'blit'),(0x2199,'cheer'),(0x02D6,'dump'),(0x8348,'bg')]:
    c.hooks[a]=mk(n)
s.run(30)
import collections
print(log[:60])
