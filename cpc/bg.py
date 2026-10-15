import numpy as np
from PIL import Image
PAL=[(0,0,255),(0,0,0),(255,255,255),(255,128,128)]
def decode(buf, w=64, h=104):
    a=np.zeros((h,w*4),np.uint8)
    for y in range(h):
        row=buf[y*w:(y+1)*w]
        for b in range(w):
            v=row[b]
            for k in range(4): a[y,b*4+k]=((v>>(7-k))&1)|(((v>>(3-k))&1)<<1)
    return a
def encode(a):
    h,W=a.shape; out=bytearray()
    for y in range(h):
        for b in range(W//4):
            v=0
            for k in range(4):
                p=int(a[y,b*4+k]); v|=((p&1)<<(7-k))|(((p>>1)&1)<<(3-k))
            out.append(v)
    return bytes(out)
def img(a, sc=3):
    p=np.array(PAL,np.uint8)[a]
    return Image.fromarray(p).resize((a.shape[1]*sc,a.shape[0]*sc),Image.NEAREST)
