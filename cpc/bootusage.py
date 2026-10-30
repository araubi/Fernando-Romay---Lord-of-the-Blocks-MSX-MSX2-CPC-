import numpy as np, pickle
from sess import Sess
s=Sess(); m=s.m; c=s.c; ram=m.ram
R=np.zeros(65536,np.uint8); W=np.zeros(65536,np.uint8); X=np.zeros(65536,np.uint8)
def rd(a): a&=0xFFFF; R[a]=1; return ram[a]
def wr(a,v): a&=0xFFFF; W[a]=1; ram[a]=v&255
m.rd=rd; m.wr=wr
end=c.frames+700
while c.frames<end: X[c.PC]=1; c.step()
s.key('space')
end=c.frames+800
while c.frames<end: X[c.PC]=1; c.step()
pickle.dump((R,W,X),open('/tmp/claude-0/usage_boot.pkl','wb'))
for lo,hi in [(0x8000,0x8118),(0xA568,0xBB56),(0x7C00,0x8000),(0x0,0x226)]:
    xs=[a for a in range(lo,hi) if X[a]]; rs=[a for a in range(lo,hi) if R[a] and not X[a]]; ws=[a for a in range(lo,hi) if W[a]]
    print('%04X-%04X exec %d [%s] read %d [%s..%s] write %d'%(lo,hi,len(xs),hex(min(xs)) if xs else '',len(rs),hex(min(rs)) if rs else '',hex(max(rs)) if rs else '',len(ws)))
