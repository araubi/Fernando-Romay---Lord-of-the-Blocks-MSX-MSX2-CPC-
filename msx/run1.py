import sys, time
from msx import *
from common import CAS
m,c=load_from_cas(open(CAS,'rb').read())
print('en 84D0, ppi %02X'%m.ppi_a)
shots=[]
def onf(cpu):
    if cpu.frames%25==0: shots.append((cpu.frames, m.vdp.render()))
c.on_frame=onf
t=time.time()
c.run(int(sys.argv[1]) if len(sys.argv)>1 else 3_000_000)
print('frames',c.frames,'PC %04X'%c.PC,'im',c.im,'iff',c.iff,'%.1fs'%(time.time()-t), 'regs',m.vdp.reg)
W=len(shots); cols=4
if shots:
    sheet=Image.new('RGB',(256*cols,(192+12)*((W+cols-1)//cols)),(60,60,60))
    for i,(f,im) in enumerate(shots): sheet.paste(im,((i%cols)*256,(i//cols)*204))
    sheet.save('sheet.png')
