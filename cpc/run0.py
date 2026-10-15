import sys, cpcemu
F=cpcemu.load_disk('in/orig.dsk')
m,c=cpcemu.boot(F)
seen=[]
def pl(cpu,p,v):
    if len(seen)<60: seen.append((hex(cpu.PC),hex(p),hex(v)))
c.portlog=pl
pcs={}
for i in range(int(sys.argv[1])):
    c.step()
    if c.PC>=0xB900 and c.PC<0xC000 and c.PC not in pcs: pcs[c.PC]=i
print('frames',c.frames,'PC %04X'%c.PC, 'SP %04X'%c.SP)
print(seen[:60])
print({hex(k):v for k,v in list(pcs.items())[:20]})
import pickle
cpcemu.render(m).save('/tmp/claude-0/cpc0.png')
