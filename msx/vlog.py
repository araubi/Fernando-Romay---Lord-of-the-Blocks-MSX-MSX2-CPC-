import collections
from msx import *
from common import CAS
m,c=load_from_cas(open(CAS,'rb').read())
c.run(600000)   # dejar que arranque
print('frame',c.frames)
agg=collections.defaultdict(lambda:[1<<20,-1,0])
def lg(a,v):
    e=agg[m.vdp.pc]; e[0]=min(e[0],a); e[1]=max(e[1],a); e[2]+=1
m.vdp.log=lg
c.run(1500000)
for pc,(lo,hi,n) in sorted(agg.items()):
    print('PC %04X  VRAM %04X-%04X  escrituras %d'%(pc,lo,hi,n))
