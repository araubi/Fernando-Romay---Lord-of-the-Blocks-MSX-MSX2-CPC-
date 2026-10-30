import build, random
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100)
c=s.c; m=s.m; bad=set()
def h(cpu):
    r=m.ram; key=(r[0x85C6],r[0x85C7],r[0x85C8],r[0x85C9])
    if key[2]+key[3]>64 or key[0]+key[1]>104: bad.add(key+(hex(m.ram[cpu.SP+2]|m.ram[cpu.SP+3]<<8),))
    return False
c.hooks[L['DREC']]=h
def hc(cpu):
    if cpu.L not in (0x0B,0x20): bad.add(('chx',cpu.L))
    return False
c.hooks[L['CHX']]=hc
s.run(1500)
print(sorted(bad)[:20])
