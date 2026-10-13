import numpy as np
from PIL import Image, ImageDraw
from court import court_bits, put_bits
CX, CY, K = 128, 84.5, 0.42          # centro del circulo y aplastamiento de la perspectiva
def star_poly(R=30, r=12):
    pts=[]
    for i in range(10):
        a=np.radians(-90+36*i); rr=R if i%2==0 else r
        pts.append((CX+rr*np.cos(a), CY+rr*np.sin(a)*K))
    return pts
def logo_layers(R=30, r=12, trail=26):
    W,H=256,112
    star=Image.new('L',(W*4,H*4),0); d=ImageDraw.Draw(star)
    d.polygon([(x*4,y*4) for x,y in star_poly(R,r)],fill=255)
    star=np.asarray(star.resize((W,H),Image.BOX))>127
    circ=Image.new('L',(W*4,H*4),0); ImageDraw.Draw(circ).ellipse([(CX-18)*4,(CY-7.5)*4,(CX+18)*4,(CY+7.5)*4],fill=255)
    circ=np.asarray(circ.resize((W,H),Image.BOX))>127
    return star,circ
def draw(bits, R=30, r=12, trail=26, disk=True):
    b=bits.copy()
    star,circ=logo_layers(R,r,trail)
    yy,xx=np.mgrid[0:112,0:256]
    stripe=(yy%2==0)
    # estelas: cada franja se prolonga hacia la izquierda desde el borde de la estrella
    ys=np.where(star.any(1))[0]; y0,y1=ys.min(),ys.max()
    trails=np.zeros_like(star)
    for y in range(y0,y1+1):
        xs=np.where(star[y])[0]
        if not len(xs): continue
        left=xs.min(); t=1-abs(y-CY)/((y1-y0)/2+1)
        L=int(round(trail*max(t,0)))
        trails[y,max(0,left-L):left]=True
    paint=(star|trails)&stripe&~circ
    b|=paint
    # circulo: trama como las zonas (disco), conservando contorno y linea central
    inner=circ.copy(); inner[1:-1,1:-1]=circ[1:-1,1:-1]&circ[:-2,1:-1]&circ[2:,1:-1]&circ[1:-1,:-2]&circ[1:-1,2:]
    if disk:
        b[inner]=((yy+xx)%2==0)[inner]
        b|=bits&circ                     # conservar el contorno original del circulo
    b[:,128]|=(yy>=65)[:,0]&(yy<=110)[:,0]
    # aros olimpicos
    rings=Image.new('L',(256*4,112*4),0); d=ImageDraw.Draw(rings)
    for cx,cy in ((114,103.5),(128,103.5),(142,103.5),(121,106.5),(135,106.5)):
        d.ellipse([(cx-6.5)*4,(cy-2.6)*4,(cx+6.5)*4,(cy+2.6)*4],outline=255,width=4)
    rings=np.asarray(rings.resize((256,112),Image.BOX))>90
    b|=rings
    return b
PARAMS=dict(R=40,r=16,trail=20,disk=False)
def apply(F1,F2,F3):
    b=court_bits(F3); put_bits(F3,draw(b,**PARAMS))
if __name__=='__main__':
    from common import files
    _,_,F=files(); b=court_bits(F['f3'][3]); nb=draw(b)
    im=Image.fromarray(((~nb)*255).astype('uint8')).crop((60,60,200,112)).resize((560,208),Image.NEAREST); im.save('court_logo.png')
