import build
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1')
c=s.c; m=s.m
log=[]
c.hooks[L['FULLH']]=lambda cpu:(log.append(('full',cpu.frames)),False)[1]
c.hooks[L['ERASE']]=lambda cpu:(log.append(('erase',cpu.frames,bytes(m.ram[0x7354:0x7386]).hex(), m.ram[0x7384]|m.ram[0x7385]<<8)),False)[1]
c.hooks[L['RECT']]=lambda cpu:(log.append(('rect',cpu.B,cpu.C,cpu.E,cpu.A,hex(cpu.gHL()),hex(cpu.IX))),False)[1]
while not any(x[0]=='erase' for x in log): c.step()
s.run(3)
for x in log[:30]: print(x)
