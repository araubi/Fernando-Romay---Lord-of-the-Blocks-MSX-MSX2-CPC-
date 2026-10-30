import os, sys, random, collections
os.environ.setdefault('MSX_FRAME','71364')
from session import *
from PIL import Image
def longrun(cas, frames, seed=11, every=600, tag='lr'):
    rnd=random.Random(seed); sc=press('SPACE',120)+press('1',340)+press(os.environ.get('CHOICE','1'),400); f=460
    while f<frames:
        k=rnd.choice(['RIGHT','LEFT','UP','DOWN','SPACE','SPACE','RIGHT','LEFT','UP']); d=rnd.randint(5,70)
        sc+=[(f,k,True),(f+d,k,False)]; f+=d+rnd.randint(1,8)
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(sc)
    last_main=[-999]; stale=[]; shots=[]; mism=[0,0]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        v=m.vdp.vram
        vis=m.vdp.reg[1]&0x40 and v[0x1B00]!=0xD0 and any(v[0x1B00+4*i]<0xC0 or v[0x1B00+4*i]>=0xE0 for i in range(12))
        if vis and cpu.frames-last_main[0]>12: stale.append(cpu.frames)
        if cpu.frames%every==0: shots.append((cpu.frames,m.vdp.render()))
    def mh(cpu): last_main[0]=cpu.frames; return False
    c.hooks[0x8554]=mh; c.on_frame=onf
    while c.frames<frames: c.step()
    return stale, shots, c
if __name__=='__main__':
    cas=sys.argv[1]; N=int(sys.argv[2])
    stale,shots,c=longrun(cas,N)
    print('PC final %04X'%c.PC, 'fotogramas con sprites fuera del bucle:',len(stale), stale[:20])
    W=4; H=(len(shots)+W-1)//W
    sheet=Image.new('RGB',(256*W,192*H))
    for i,(f,im) in enumerate(shots): sheet.paste(im,((i%W)*256,(i//W)*192))
    sheet.save('../out/long_%s.png'%os.path.basename(cas))
