import numpy as np
from PIL import Image, ImageOps, ImageFilter
SRC='/mnt/user-data/uploads/1791806141505_image.png'
def trace(W=38,H=46,box=(18,0,261,300),mirror=True,thr_bg=205,thr_dark=85,line_frac=0.28,hair_frac=0.5):
    im=Image.open(SRC).convert('RGB').crop(box)
    if mirror: im=ImageOps.mirror(im)
    a=np.asarray(im).astype(float)
    r,g,b=a[...,0],a[...,1],a[...,2]
    lum=0.299*r+0.587*g+0.114*b
    mx=a.max(-1); mn=a.min(-1); sat=(mx-mn)/(mx+1e-6)
    bg=(lum>thr_bg)&(sat<0.18)
    dark=lum<thr_dark
    hair=dark
    # downscale por fracciones
    def frac(m):
        return np.asarray(Image.fromarray((m*255).astype('uint8')).resize((W,H),Image.BOX)).astype(float)/255
    fbg=frac(bg); fd=frac(dark)
    return fbg,fd
if __name__=='__main__':
    fbg,fd=trace()
    W,H=38,46
    out=np.zeros((H,W),bool)
    sil=fbg<0.5
    out=sil&(fd<0.45)
    Image.fromarray((out*255).astype('uint8')).resize((W*12,H*12),Image.NEAREST).save('trace.png')
    g=Image.fromarray(((1-fd)*255*sil).astype('uint8')).resize((W*12,H*12),Image.NEAREST).save('trace_gray.png')
