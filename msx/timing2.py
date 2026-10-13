import sys, statistics
from timing import *
def t2(cas, f0=450, f1=1300, seed=2):
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(script(f1,seed))
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; T=[]; last=[None]
    def h(cpu):
        if cpu.frames>=f0:
            if last[0] is not None: T.append(cpu.cyc-last[0])
            last[0]=cpu.cyc
        return False
    c.hooks[0x8554]=h
    while c.frames<f1: c.step()
    T2=[t for t in T if t<600000]
    return statistics.median(T2), statistics.mean(T2), len(T2)
if __name__=='__main__':
    for f in sys.argv[1:]:
        md,mn,n=t2(f); print('%-12s mediana %6.0f ciclos (%.2f int)  media %6.0f  n=%d'%(f,md,md/59659,mn,n))
