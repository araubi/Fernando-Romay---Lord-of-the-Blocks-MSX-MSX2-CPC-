import numpy as np
from PIL import Image, ImageDraw
import court_patch as CP
def star_mask(R,r,dx=0,dy=0):
    W,H=256,112
    im=Image.new('L',(W*4,H*4),0); d=ImageDraw.Draw(im)
    d.polygon([((x+dx)*4,(y+dy)*4) for x,y in CP.star_poly(R,r)],fill=255)
    return np.asarray(im.resize((W,H),Image.BOX))>127
def shadow(bits, mode='outline', dx=12, dy=0):
    P=CP.PARAMS; b=bits.copy()
    star=star_mask(P['R'],P['r']); sh=star_mask(P['R'],P['r'],dx,dy)
    _,circ=CP.logo_layers(P['R'],P['r'])
    yy,xx=np.mgrid[0:112,0:256]
    reg=sh&~star&~circ&(xx>CP.CX)
    if mode=='outline':
        ero=sh.copy(); ero[1:-1,1:-1]=sh[1:-1,1:-1]&sh[:-2,1:-1]&sh[2:,1:-1]&sh[1:-1,:-2]&sh[1:-1,2:]
        b|=reg&~ero
    elif mode=='dither':
        b|=reg&((yy+xx)%2==0)
    elif mode=='stripes_odd':
        b|=reg&(yy%2==1)&(xx%2==0)
    elif mode=='sparse':
        b|=reg&(yy%2==0)&(xx%2==0)
    return b
if __name__=='__main__':
    import pickle
    vr,ram=pickle.load(open('state460.pkl','rb'))
    base=np.unpackbits(np.frombuffer(ram[0xB498:0xB498+32*112],np.uint8)).reshape(112,256).astype(bool)
    ims=[]
    for mode,dx in (('outline',10),('outline',14),('sparse',12),('dither',12)):
        b=shadow(base,mode,dx)
        ims.append(Image.fromarray(((~b)*255).astype('uint8')).crop((60,56,200,112)).resize((140*4,56*4),Image.NEAREST))
    sheet=Image.new('L',(140*4*2+10,56*4*2+10),128)
    for i,im in enumerate(ims): sheet.paste(im,((i%2)*(140*4+10),(i//2)*(56*4+10)))
    sheet.save('/tmp/claude-0/sh.png')
def shadow2(bits, dx=12):
    a=shadow(bits,'outline',dx); s=shadow(bits,'sparse',dx); return a|s
def apply(F1,F2,F3):
    from court import court_bits, put_bits
    put_bits(F3, shadow2(court_bits(F3)))
