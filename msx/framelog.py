import collections, random
from session import *
KEY.update({'D':(3,1),'F':(3,3),'Q':(4,6),'Z':(5,7)})
def framelog(cas, frames=3000, seed=3):
    rnd=random.Random(seed)
    sc=press('SPACE',120)+press('1',340)
    f=420
    while f<frames:
        k=rnd.choice(['D','F','1','Q','Z','D','F']); d=rnd.randint(5,60)
        sc+= [(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,10)
    m,c=load_from_cas(cas)
    ev=sorted(sc); log=collections.Counter()
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; m.slot=lambda p:0
    def hk(cpu):
        side=None
        if cpu.IX in (0x940B,0x9425): side=cpu.m.ram[cpu.IX+1]&1
        log[(cpu.A,side, cpu.m.rd(cpu.SP)|cpu.m.rd(cpu.SP+1)<<8)]+=1
        return False
    c.hooks[0x9E6F]=hk
    while c.frames<frames: c.step()
    return log
if __name__=='__main__':
    out=open('/mnt/user-data/outputs/Fernando_Martin_Basket_Master_NIDAMIC.cas','rb').read()
    log=framelog(out)
    by=collections.defaultdict(set)
    for (a,side,ret),n in log.items(): by[a].add((side,ret))
    for a in sorted(by): print('idx %02X'%a, sorted((s if s is not None else -1,'%04X'%r) for s,r in by[a]))
