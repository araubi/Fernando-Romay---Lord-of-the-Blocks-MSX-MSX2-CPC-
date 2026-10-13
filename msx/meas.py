import sys
from session import *
from mk import make
def meas(cas, keys, frames=2400):
    sc=press('SPACE',120)+press('1',340)
    f=420; i=0
    while f<frames:
        k=keys[i%len(keys)]; sc+=[(f,k,True),(f+80,k,False)]; f+=81; i+=1
    m,c=load_from_cas(cas); ev=sorted(sc); E=[]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        E.append((m.ram[0x940B+10],m.ram[0x9425+10],m.ram[0x940B+3],m.ram[0x940B+2]))
    c.on_frame=onf; m.slot=lambda p:0
    while c.frames<frames: c.step()
    return E
if __name__=='__main__':
    for name,cas in (('base',make(('stats_patch',))),('stats',make())):
        E=meas(cas,['RIGHT','LEFT','UP','DOWN'])
        e1=[e[0] for e in E]
        first=[next((i for i,v in enumerate(e1) if v<=e1[430]-k),None) for k in (2,4,6,8,10)]
        print(name,'e1@430',e1[430],'drop frames',first, 'e2 seq', [E[i][1] for i in range(430,2400,200)])
