from common import *
from PIL import Image
_,_,F=files(); s2,e2,x2,b2=F['f2']
def title_addr(e740_addr): return e740_addr-0xE740+0xC394
def get(addr_e,w,h):
    a=title_addr(addr_e)-s2
    return [[bool(b2[a+y*w+x//8]&(0x80>>(x%8))) for x in range(w*8)] for y in range(h)]
def img(bits,fg=(255,255,255),bg=(0,0,0)):
    h=len(bits); w=len(bits[0]); im=Image.new('RGB',(w,h)); p=im.load()
    for y in range(h):
        for x in range(w): p[x,y]=fg if bits[y][x] else bg
    return im
if __name__=='__main__':
    for nm,a,w,h in (('titulo',0xE740,30,16),('executive',0xE920,30,40),('version',0xEDD0,30,32),('f190',0xF190,30,8)):
        img(get(a,w,h)).resize((w*8*4,h*4),Image.NEAREST).save('m_%s.png'%nm)
