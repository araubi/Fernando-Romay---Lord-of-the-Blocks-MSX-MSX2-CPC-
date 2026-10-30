import os, sys, random, time
os.environ.setdefault('MSX_FRAME','71364')
from msx2emu import *
from session import KEY, press
from PIL import Image
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2]); ch=sys.argv[3] if len(sys.argv)>3 else '1'
rnd=random.Random(7); sc=press('SPACE',120)+press('1',340)+press(ch,420); f=470
while f<N:
    k=rnd.choice(['RIGHT','LEFT','UP','DOWN','SPACE','SPACE','RIGHT','LEFT','UP']); d=rnd.randint(5,70)
    sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,8)
m,c=boot2(rom); m.slot=lambda p:0; ev=sorted(sc); shots=[]; over=[0]; last=[0]; stale=[0]
def onf(cpu):
    while ev and ev[0][0]<=cpu.frames:
        _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    if cpu.frames%500==0:
        im=m.vdp.render(); over[0]+=getattr(m.vdp,'over',0); shots.append((cpu.frames,im))
        print(cpu.frames,'PC %04X'%cpu.PC,'over',getattr(m.vdp,'over',0),'%.0fs'%(time.time()-t0),flush=True)
def mh(cpu): last[0]=cpu.frames; return False
c.on_frame=onf; t0=time.time()
while c.frames<N: c.step()
W=6; H=(len(shots)+W-1)//W; S=Image.new('RGB',(256*W,192*H))
for i,(f,im) in enumerate(shots): S.paste(im,((i%W)*256,(i//W)*192))
S.save('../out/long2_%s.png'%ch); print('fin, over total',over[0])
