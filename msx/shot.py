from PIL import Image
import numpy as np
P='/root/.claude/uploads/4bde1580-c873-5012-b5b7-94b5463a9c6b/5a6ddbad-image.png'
L=np.asarray(Image.open(P).convert('L')).astype(float)
def sample(sx,ox,oy=48,sy=2.0,mode='center'):
    """media de luminancia de la caja de cada pixel MSX"""
    out=np.zeros((192,256))
    for y in range(192):
        y0=int(round(oy+y*sy)); y1=int(round(oy+(y+1)*sy))
        for x in range(256):
            x0=int(round(ox+x*sx)); x1=max(x0+1,int(round(ox+(x+1)*sx)))
            out[y,x]=L[y0:y1,x0:x1].mean()
    return out
