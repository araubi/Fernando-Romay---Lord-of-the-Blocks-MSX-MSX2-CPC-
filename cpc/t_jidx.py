import build, random, collections
from sess import Sess
im=build.make()
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
for k in range(3): s.key('3'); s.run(30)
s.key('1'); s.run(60); s.key('1'); s.run(150)
cnt=collections.Counter(); st={'prev':s.m.ram[0x114C],'dir':None}
def h(cpu):
    if cpu.IX==0x1149 and cpu.A in (0x0A,0x0B,0x16,0x17,0x22,0x23,0x2E,0x2F):
        cnt[(st['dir'],hex(cpu.A))]+=1
    return False
s.c.hooks[0x1BC0]=h
def onf(cpu):
    hh=s.m.ram[0x114C]; st['dir']='R' if hh>st['prev'] else ('L' if hh<st['prev'] else '0'); st['prev']=hh
s.c.on_frame=onf
s.run(1500)
for k,v in sorted(cnt.items(), key=str): print(k,v)
