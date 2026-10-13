import random, sys
from session import *
def script(frames, seed=2):
    rnd=random.Random(seed); sc=press('SPACE',120)+press('1',340); f=420
    while f<frames:
        k=rnd.choice(['RIGHT','LEFT','UP','DOWN','SPACE','RIGHT','LEFT']); d=rnd.randint(8,50)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,6)
    return sc
def timing(cas, f0=500, f1=1500, seed=2, extra_hooks=None):
    m,c=load_from_cas(cas); m.slot=lambda p:0; ev=sorted(script(f1,seed))
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; n=[0]
    def h(cpu):
        if f0<=cpu.frames<f1: n[0]+=1
        return False
    c.hooks[0x8554]=h
    for a,f in (extra_hooks or {}).items(): c.hooks[a]=f
    while c.frames<f1: c.step()
    return n[0], (f1-f0)/max(n[0],1), m, c
if __name__=='__main__':
    n,per,m,c=timing(open(sys.argv[1],'rb').read())
    print('iteraciones',n,'interrupciones por fotograma de juego %.2f'%per, 'fps %.1f'%(50/per), '(a 50 Hz)')
