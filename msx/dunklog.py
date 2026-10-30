import collections
from session import *
from sprites import entry, p1
def table_spans():
    sp=[]
    for i in range(0x50):
        e=entry(i); h=p1(e); w=p1(e+1); sp.append((e,e+2+h*w,i))
    return sp
def run_log(cas, frames, script=None):
    m,c=load_from_cas(cas)
    ev=sorted(script or (press('SPACE',120)+press('1',340))); logs=collections.OrderedDict(); shots={}
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; m.slot=lambda p:0
    def hk(cpu):
        r=cpu.m.ram; src=r[0xD09A]|r[0xD09B]<<8
        st=tuple(cpu.m.rd(cpu.SP+2*k)|cpu.m.rd(cpu.SP+2*k+1)<<8 for k in range(4))
        key=(src,st[0])
        if key not in logs: logs[key]=(cpu.frames,st)
        return False
    c.hooks[0xB113]=hk
    while c.frames<frames: c.step()
    return logs
if __name__=='__main__':
    out=open('../releases/Fernando_Romay_Lord_of_the_Blocks_MSX1.cas','rb').read()
    logs=run_log(out,6000)
    sp=table_spans()
    for (src,r0),(f,st) in logs.items():
        idx=[('%02X+%d'%(i,src-a)) for a,b,i in sp if a<=src<b]
        print('f%5d src %04X %s pila %s'%(f,src,idx or '-',' '.join('%04X'%x for x in st)))
