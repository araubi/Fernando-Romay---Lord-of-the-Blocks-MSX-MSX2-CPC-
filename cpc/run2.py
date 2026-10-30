import cpcemu, collections
F=cpcemu.load_disk('in/orig.dsk')
m,c=cpcemu.boot(F)
ring=collections.deque(maxlen=40)
n=0; started=False
while c.frames<320:
    pc=c.PC
    if pc==0x226: started=True
    if pc>=0xC000 and not (0xBFCC<=pc<0xBFF1):
        print('n',n,'frame',c.frames); break
    ring.append((pc,c.SP,c.frames)); c.step(); n+=1
import dz80
for pc,sp,f in ring: print('%04X sp=%04X f=%d %s'%(pc,sp,f,dz80.dis(m.ram,pc)[0]))
