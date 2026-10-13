import random, pickle, sys
from session import *
def go(cas, frames, seed=1):
    rnd=random.Random(seed)
    sc=press('SPACE',120)+press('1',340); f=420
    keys=['RIGHT','LEFT','UP','DOWN','SPACE','SPACE','RIGHT','LEFT']
    while f<frames:
        k=rnd.choice(keys); d=rnd.randint(5,50)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,6)
    m,c=load_from_cas(cas); ev=sorted(sc)
    W=bytearray(65536); R=bytearray(65536); X=bytearray(65536)
    loaded=[False]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; m.slot=lambda p:0
    ord_,owr=m.rd,m.wr
    def rd(a):
        a&=0xFFFF; R[a]=1; return ord_(a)
    def wr(a,v):
        a&=0xFFFF; W[a]=1; return owr(a,v)
    m.rd=rd; m.wr=wr
    while c.frames<frames: c.step()
    return R,W
if __name__=='__main__':
    R,W=go(open('nidamic.cas','rb').read(), int(sys.argv[1]))
    pickle.dump((bytes(R),bytes(W)),open('memmap.pkl','wb'))
    # zonas sin uso >= 64 bytes en C000-FFFF y 8000-BFFF
    run=None
    for a in range(0x8000,0x10000):
        u=R[a] or W[a]
        if not u and run is None: run=a
        if (u or a==0xFFFF) and run is not None:
            if a-run>=48: print('%04X-%04X %d'%(run,a-1,a-run))
            run=None
