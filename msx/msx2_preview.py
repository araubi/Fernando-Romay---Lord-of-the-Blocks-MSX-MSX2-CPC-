import os
os.environ.setdefault('MSX_FRAME','71364')
from session import *
from msx2pal import *
from PIL import Image
def preview(cas, script, shots, choice_romay=False):
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(script)
    cur=[]; done=[]; res={}
    def blit(cpu):
        i=m.ram[0x8246]
        if i<0x3E and cpu.IX in (0x940B,0x9425):
            cur.append((i,m.ram[0xD099],m.ram[0xD098],cpu.IX))
        return False
    def loop(cpu):
        done[:]=cur[:]; cur.clear(); return False
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        if cpu.frames in shots:
            im=m.vdp.render(sprites=False); px=im.load()
            for i,x,y,ix in done:
                left= ix==0x940B
                M = ITU if (left!=choice_romay) else ROM
                rows=resolved(i,M); X0=(x if x<128 else x-256)*2; Y0=y+8
                for yy,row in enumerate(rows):
                    for xx,cl in enumerate(row):
                        if isinstance(cl,int):
                            X,Y=X0+xx,Y0+yy
                            if 0<=X<256 and 8<=Y<120 and px[X,Y]!=(0,0,0) : px[X,Y]=rgb(cl)
            res[cpu.frames]=im
    c.hooks[0xB01C]=blit; c.hooks[0x8554]=loop; c.on_frame=onf
    while c.frames<max(shots)+1: c.step()
    return res
if __name__=='__main__':
    sc=press('SPACE',120)+press('1',340)+press('1',420)
    import random; rnd=random.Random(4); f=470
    while f<1500:
        k=rnd.choice(['RIGHT','LEFT','UP','DOWN','SPACE']); d=rnd.randint(8,40); sc+=[(f,k,True),(f+d,k,False)]; f+=d+3
    shots=(520,700,860,1020,1180,1400)
    r=preview('fin2.cas',sc,shots)
    S=Image.new('RGB',(512*3,256*2+8),(30,30,30))
    for k,f in enumerate(shots): S.paste(r[f].crop((0,8,256,136)).resize((512,256),Image.NEAREST),((k%3)*512,(k//3)*(256+8)))
    S.save('../out/MSX2_vista_previa.png')
