import collections, random, sys
from session import *
def play(cas, frames=4000, seed=3, watch=None, hooks=None):
    rnd=random.Random(seed)
    sc=press('SPACE',120)+press('1',340); f=420
    while f<frames:
        k=rnd.choice(['RIGHT','LEFT','UP','DOWN','SPACE','SPACE']); d=rnd.randint(5,60)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,10)
    m,c=load_from_cas(cas); ev=sorted(sc)
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; m.slot=lambda p:0
    acc=collections.Counter()
    if watch:
        lo,hi=watch; ord_,owr=m.rd,m.wr
        def rd(a):
            if lo<=a<=hi: acc[('r',a)]+=1
            return ord_(a)
        def wr(a,v):
            if lo<=a<=hi: acc[('w',a)]+=1
            return owr(a,v)
        m.rd=rd; m.wr=wr
    for a,h in (hooks or {}).items(): c.hooks[a]=h
    while c.frames<frames: c.step()
    return m,c,acc
if __name__=='__main__':
    cas=open('nidamic.cas','rb').read()
    shots=[]
    def h(cpu): shots.append((cpu.frames,cpu.m.ram[0x93EB]>>7)); return False
    m,c,acc=play(cas,watch=(0xAF9A,0xAFC7),hooks={0x8B32:h})
    print('accesos',dict(acc)); print('tiros',shots)
