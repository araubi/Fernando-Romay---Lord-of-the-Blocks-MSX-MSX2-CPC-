import numpy as np
from menugfx import get, img
import brush
E920=0xE920; E740=0xE740
def new_exec_bitmap():
    b=np.array(get(E920,30,40))          # True = fondo (cian), False = trazo negro
    nb=b.copy()
    keep=np.zeros_like(b)
    keep[0:3,:]=True
    keep[:, :8]=True; keep[:, 224:]=True
    keep[3:11, 64:146]=True              # (c) DINAMIC 1987
    keep[3:21, 198:225]=True             # estrella
    nb[~keep]=True
    LAY=[('Lord','big',8,36),('of the','small',76,36),('blocks','big',124,36)]
    t=brush.render(LAY,size=(224,40),w_big=5.0,w_small=2.8)
    full=np.zeros_like(b); full[:, :224]=t
    full[keep]=False
    nb[full]=False
    # (c) DINAMIC -> (c) NIDAMIC: intercambiar los glifos D (x 75-79) y N (x 83-87)
    d=nb[3:11,75:80].copy(); n=nb[3:11,83:88].copy()
    nb[3:11,75:80]=n; nb[3:11,83:88]=d
    return nb
def title_row():
    b=np.array(get(E740,30,16))
    cell=lambda i: b[:, i*16:(i+1)*16].copy()
    Y=cell(13).copy()                     # casilla de la I: fondo + borde
    Y[8:15,6:13]=True
    for x,y in ((6,8),(12,8),(7,9),(11,9),(8,10),(10,10),(9,11),(9,12),(9,13),(9,14)): Y[y,x]=False
    order=[0,1,2,3,4,5,6,7,8,8,11,7,9,10,'Y']
    out=np.concatenate([Y if i=='Y' else cell(i) for i in order],axis=1)
    return out
def to_bytes(bits):
    h,w=bits.shape; out=bytearray()
    for y in range(h):
        for bx in range(w//8):
            v=0
            for k in range(8):
                if bits[y,bx*8+k]: v|=0x80>>k
            out.append(v)
    return bytes(out)
def apply(F1,F2,F3):
    base=0xC394-0x8534       # F2: datos que acaban en E740h
    t=to_bytes(title_row()); F2[base:base+len(t)]=t
    e=to_bytes(new_exec_bitmap()); F2[base+0x1E0:base+0x1E0+len(e)]=e
    # rectangulo rojo del logo: 2 -> 4 tiles de ancho (LD BC,0410h en A56Ch)
    a=0xA56C-0x84D0; assert bytes(F3[a:a+3])==bytes([0x01,0x10,0x02]); F3[a+2]=0x04
if __name__=='__main__':
    from PIL import Image
    img(title_row()).resize((960,64),Image.NEAREST).save('m_titulo_new.png')
    img(new_exec_bitmap()).resize((960,160),Image.NEAREST).save('m_exec_new.png')

EDD0=0xEDD0
def new_version_bitmap():
    b=np.array(get(EDD0,30,32))
    for y in range(1,22):
        cut=22 if y<=12 else 17
        for x in range(10,cut): b[y,x]=True
    return b
_apply_old=apply
def apply(F1,F2,F3):
    _apply_old(F1,F2,F3)
    base=0xC394-0x8534+(EDD0-E740)
    v=to_bytes(new_version_bitmap()); F2[base:base+len(v)]=v
