from msx import *
from mk import make
def err(cas, p1, dist, timing, energy, conf):
    m,c=load_from_cas(cas); m.slot=lambda p:0
    while c.frames<500: c.step()
    r=m.ram; r[0x93EB]=(r[0x93EB]&0x7F)|(0x80 if p1 else 0)
    r[0x944F]=dist; r[0x9450]=timing; r[0x944E]=energy; r[0x944D]=conf
    c.PC=0x8B32; c.iff=0; out={}
    def stop(cpu): out['L']=cpu.L; out['H']=cpu.H; raise StopIteration
    c.hooks[0x8B8A]=stop
    try:
        for _ in range(200000): c.step()
    except StopIteration: pass
    return out['H']<<8|out['L']
def ref(dist,timing,energy,conf,p1,new):
    e=dist*(55 if (new and not p1) else 50)//70 + timing*35//8 + (22-energy)*10//23 + (50-conf)*5//50
    return e*9//10 if (new and p1) else e
base=make(('shot_patch',)); new=make()
for args in ((20,1,22,50),(40,3,10,20),(70,8,0,0),(5,2,15,30)):
    for p1 in (1,0):
        print(args,'P1' if p1 else 'P2','orig',err(base,p1,*args),ref(*args,p1,False),'nuevo',err(new,p1,*args),ref(*args,p1,True))
