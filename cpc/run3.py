import cpcemu, collections, dz80
F=cpcemu.load_disk('in/orig.dsk')
m,c=cpcemu.boot(F)
ring=collections.deque(maxlen=30)
n=0
while c.frames<320:
    pc=c.PC
    if pc<0x19A and n>10:
        print('n',n,'frame',c.frames); break
    ring.append((pc,c.SP,c.frames,c.A,c.gHL())); c.step(); n+=1
for pc,sp,f,a,hl in ring: print('%04X sp=%04X f=%d a=%02X hl=%04X %s'%(pc,sp,f,a,hl,dz80.dis(m.ram,pc)[0]))
