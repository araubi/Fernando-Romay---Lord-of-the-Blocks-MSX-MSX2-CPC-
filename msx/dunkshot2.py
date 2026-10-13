import random
from session import *
KEY.update({'D':(3,1),'F':(3,3),'Q':(4,6),'Z':(5,7)})
def script(frames,seed):
    rnd=random.Random(seed); sc=press('SPACE',120)+press('1',340); f=420
    while f<frames:
        k=rnd.choice(['D','F','1','Q','Z','D','F']); d=rnd.randint(5,60)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,10)
    return sc
def shots_jump(cas, frames, seed, maxshots=8):
    m,c=load_from_cas(cas); ev=sorted(script(frames,seed)); caps=[]; pend=[]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        if pend and len(caps)<maxshots:
            idx,side=pend.pop(0); caps.append((idx,side,cpu.frames,m.vdp.render())); pend.clear()
    c.on_frame=onf; m.slot=lambda p:0
    last=[-100]
    def hk(cpu):
        if 0x30<=cpu.A<=0x3D and cpu.frames-last[0]>10:
            last[0]=cpu.frames; pend.append((cpu.A, cpu.m.ram[cpu.IX+1]&1 if cpu.IX in (0x940B,0x9425) else -1))
        return False
    c.hooks[0x9E6F]=hk
    while c.frames<frames and len(caps)<maxshots: c.step()
    return caps
