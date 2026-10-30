import sys, pickle, random, numpy as np, time
from sess import Sess, KEY
import cpcemu
seed=int(sys.argv[1]); N=int(sys.argv[2]); mode=sys.argv[3]
s=Sess.load('../out/cpc_menu.pkl')
R=np.zeros(65536,np.uint8); W=np.zeros(65536,np.uint8); X=np.zeros(65536,np.uint8)
m=s.m; c=s.c
ram=m.ram
class M2(cpcemu.CPC): pass
def rd(a): a&=0xFFFF; R[a]=1; return ram[a]
def wr(a,v): a&=0xFFFF; W[a]=1; ram[a]=v&255
m.rd=rd; m.wr=wr
s.key(mode); 
rnd=random.Random(seed); f=c.frames+100
while f<c.frames+N:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60)
    s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
t=time.time()
end=c.frames+N
while c.frames<end:
    X[c.PC]=1; c.step()
    if c.frames%5000==0 and c.frames!=getattr(s,'_lf',0):
        s._lf=c.frames; s.shot('../out/us_%s_%d.png'%(mode,c.frames)); print(c.frames,time.time()-t,flush=True)
pickle.dump((R,W,X),open('../out/usage_%s_%d.pkl'%(mode,seed),'wb'))
s.save('../out/cpc_end_%s.pkl'%mode)
