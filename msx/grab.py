from PIL import Image
import numpy as np
P='../art/'
def msxgrid(f, sx=584/128, sy=4.0):
    L=np.asarray(Image.open(P+f).convert('L')).astype(float)
    best=None
    for ox in np.arange(0,sx,0.5):
        for oy in np.arange(0,sy,0.5):
            nx=int((640-ox)/sx); ny=int((480-oy)/sy)
            xs=(ox+(np.arange(nx)+0.5)*sx).astype(int); ys=(oy+(np.arange(ny)+0.5)*sy).astype(int)
            g=L[np.ix_(ys,xs)]
            # nitidez: variacion dentro de cada celda baja
            xs2=(ox+(np.arange(nx)+0.15)*sx).astype(int); xs3=(ox+(np.arange(nx)+0.85)*sx).astype(int)
            e=np.abs(L[np.ix_(ys,xs2)]-L[np.ix_(ys,xs3)]).mean()
            if best is None or e<best[0]: best=(e,ox,oy,g)
    return best
