import sys
from timing import *
def mism(cas, f0=430, f1=700):
    m,c=load_from_cas(open(cas,'rb').read()); m.slot=lambda p:0; ev=sorted(script(f1,2))
    res=[]
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        if f0<=cpu.frames<f1:
            v=m.vdp.vram; reg=m.vdp.reg
            if not reg[1]&2: return
            sat=0x1B00; bad=0; tot=0
            for i in range(32):
                y,x,n,col=v[sat+4*i:sat+4*i+4]
                if y==0xD0: break
                if y>=0xC0 and y<0xE0: continue
                yy=(y+1)&255
                for row in range(16):
                    Y=yy+row
                    if not 8<=Y<120: continue
                    for cc in range(16):
                        b=v[0x3800+n*8+(row&7)+(16 if cc>=8 else 0)+(8 if row>=8 else 0)]
                        if b&(0x80>>(cc&7)):
                            X=x+cc
                            if X>255: continue
                            tot+=1
                            p=v[(Y>>3)*256+(X>>3)*8+(Y&7)]
                            if p&(0x80>>(X&7)): bad+=1
            res.append((cpu.frames,tot,bad))
    c.on_frame=onf
    while c.frames<f1: c.step()
    return res
if __name__=='__main__':
    r=mism(sys.argv[1])
    print('fotogramas',len(r),'con desajuste',sum(1 for _,t,b in r if b>0))
    print([ (f,t,b) for f,t,b in r if b>0][:30])
