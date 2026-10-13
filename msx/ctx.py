import numpy as np
from PIL import Image
from common import *
import head5
def compose(px, h, X0=48, Y0=8):
    for y in range(56):
        for x in range(32): px[Y0+y][X0+x]=15 if h[y,x] else 1
    return px
def ctx_sheet(exprs=(0,1,2,3,4,5,6,7), out='ctx.png'):
    d,pos,F=files()
    ims=[]
    for e in exprs:
        px=decode(F['f1'][3])
        for y in range(19,28): px[y][80]=1          # resto del pelo original fuera de la ventana
        compose(px, head5.build(e))
        ims.append(to_img(px).crop((0,0,120,110)).resize((360,330),Image.NEAREST))
    sheet=Image.new('RGB',(370*4,340*((len(ims)+3)//4)),(70,70,70))
    for i,im in enumerate(ims): sheet.paste(im,((i%4)*370,(i//4)*340))
    sheet.save(out)
if __name__=='__main__': ctx_sheet()
