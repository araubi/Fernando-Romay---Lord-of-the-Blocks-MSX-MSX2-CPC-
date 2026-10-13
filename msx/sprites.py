from common import *
from PIL import Image, ImageDraw
_,_,F=files(); s2,e2,x2,f2=F['f2']
def p1(addr):            # pagina 1 (415A..) <- F2 8534..
    return f2[addr-0x415A]
def entry(i):
    a=0x7760+2*i; off=p1(a)|p1(a+1)<<8; return 0x415A+off
def sprite(i):
    a=entry(i); h=p1(a); w=p1(a+1); rows=[]
    a+=2
    for y in range(h):
        d=[p1(a+k) for k in range(4)]; a+=4
        rows.append(d)
    return h,w,rows
def render(i,sc=6):
    h,w,rows=sprite(i)
    im=Image.new('RGB',(16,h),(0,160,160)); p=im.load()
    for y,(d0,d1,m0,m1) in enumerate(rows):
        for x in range(16):
            dbit=(d0 if x<8 else d1)&(0x80>>(x%8)); mbit=(m0 if x<8 else m1)&(0x80>>(x%8))
            p[x,y]=(0,0,0) if (not mbit and not dbit) else ((255,255,255) if dbit else (0,160,160))
    return im.resize((16*sc,h*sc),Image.NEAREST),(h,w)
if __name__=='__main__':
    idxs=[0x08,0x09,0x0A,0x0B,0x14,0x15,0x16,0x17,0x20,0x21,0x22,0x23,0x2C,0x2D,0x2E,0x2F,0x42,0x43]
    ims=[render(i) for i in idxs]
    W=sum(im.width+6 for im,_ in ims); H=max(im.height for im,_ in ims)+14
    s=Image.new('RGB',(W,H),(60,60,60)); d=ImageDraw.Draw(s); x=0
    for i,(im,hw) in zip(idxs,ims):
        s.paste(im,(x,14)); d.text((x,0),'%02X %dx%d'%(i,hw[0],hw[1]),fill=(255,255,0)); x+=im.width+6
    s.save('sprites.png')
