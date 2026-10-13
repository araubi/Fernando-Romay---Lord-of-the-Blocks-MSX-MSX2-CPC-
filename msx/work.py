import sys, os, statistics
os.environ.setdefault('MSX_FRAME','71364')
from timing import *
import sprite_patch as S
def work(cas, f0=450, f1=1150, seed=2):
    (ca,cb),L,(a,b)=S.build()
    hp=[pc for pc,by,t in a.lines if t=='halt'][0]
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(script(f1,seed))
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b_=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b_)) if dn else (m.keys[r]|(1<<b_))
    c.on_frame=onf; W=[]; t=[None]
    def st(cpu):
        t[0]=cpu.cyc if cpu.frames>=f0 else None; return False
    def hl(cpu):
        if t[0] is not None: W.append(cpu.cyc-t[0]); t[0]=None
        return False
    c.hooks[0x8554]=st; c.hooks[hp]=hl
    while c.frames<f1: c.step()
    return W
if __name__=='__main__':
    W=work(sys.argv[1]); fr=int(os.environ['MSX_FRAME'])
    W.sort(); n=len(W)
    print('trabajo hasta HALT: mediana %.0f (%.2f fot), p75 %.0f, p90 %.0f, max %.0f; <3 fot: %d%%'%(W[n//2],W[n//2]/fr,W[3*n//4],W[9*n//10],W[-1],100*sum(w<3*fr for w in W)//n))
