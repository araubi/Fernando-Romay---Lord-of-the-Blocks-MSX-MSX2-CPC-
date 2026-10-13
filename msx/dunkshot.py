from session import *
def shots_jump(cas, frames=6000, maxshots=6):
    m,c=load_from_cas(cas); ev=sorted(press('SPACE',120)+press('1',340)); caps=[]; pend=[]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        if pend and len(caps)<maxshots:
            idx,f=pend.pop(0); caps.append((idx,cpu.frames,m.vdp.render())); pend.clear()
    c.on_frame=onf; m.slot=lambda p:0
    last=[-100]
    def hk(cpu):
        if 0x30<=cpu.A<=0x3D and cpu.frames-last[0]>8:
            last[0]=cpu.frames; pend.append((cpu.A,cpu.frames))
        return False
    c.hooks[0x9E6F]=hk
    while c.frames<frames and len(caps)<maxshots: c.step()
    return caps
