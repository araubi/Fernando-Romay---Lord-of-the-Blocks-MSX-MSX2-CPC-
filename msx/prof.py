import collections, bisect, re, sys
from timing import *
import sprite_patch as S
def ranges():
    labs={}
    for ln in open('/mnt/user-data/outputs/basket_master_msx.asm'):
        pass
    L=[]; pend=None
    for ln in open('/mnt/user-data/outputs/basket_master_msx.asm'):
        m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*):',ln)
        if m: pend=m.group(1); continue
        m=re.search(r';\s*([0-9A-F]{4}):',ln)
        if m and pend: L.append((int(m.group(1),16),pend)); pend=None
    _,lab,_=S.build()
    for k,v in lab.items():
        if k.isupper() and not k in ('ACTIVE',): L.append((v,'*'+k))
    L.sort(); return L
def prof(cas,f0=500,f1=800):
    L=ranges(); keys=[a for a,_ in L]
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(script(f1,2))
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf
    P=collections.Counter(); last=c.cyc
    while c.frames<f1:
        pc=c.PC; c0=c.cyc; c.step()
        if c.frames>=f0:
            i=bisect.bisect_right(keys,pc)-1; P[L[i][1] if i>=0 else '?']+=c.cyc-c0
    tot=sum(P.values())
    for k,v in P.most_common(25): print('%-22s %5.1f%%'%(k,100*v/tot))
if __name__=='__main__': prof(sys.argv[1])
