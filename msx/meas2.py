import collections, random
from session import *
from mk import make
def run(cas, frames=6000, seed=5):
    rnd=random.Random(seed)
    sc=press('SPACE',120)+press('1',340); f=420
    while f<frames:
        k=rnd.choice(['RIGHT','LEFT','UP','DOWN']); d=rnd.randint(40,150)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+1
    m,c=load_from_cas(cas); ev=sorted(sc)
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; m.slot=lambda p:0
    C=collections.Counter()
    def h(tag):
        def f(cpu):
            C[(tag,'%04X'%cpu.IX, bool(m.ram[cpu.IX+9]&0x80) if tag=='call' else None)]+=1; return False
        return f
    c.hooks[0x9EE3]=h('call'); c.hooks[0x9F02]=h('dec')
    # movimiento: contar desplazamiento x/y absoluto
    pos={}
    while c.frames<frames: c.step()
    return C
for name,skip in (('base',('stats_patch',)),('stats',())):
    C=run(make(skip)); print(name,dict(C))
    for ix in ('940B','9425'):
        calls=C[('call',ix,True)]+C[('call',ix,False)]; d=C[('dec',ix,None)]
        print('  ',ix,'calls',calls,'decs',d,'ratio %.4f'%(d/calls if calls else 0))
