from common import *
from PIL import Image
d,pos,F=files(); s3,e3,x3,b3=F['f3']
mem=lambda a: b3[a-s3]
OBJS={'balon':(0xC298,3,4,32),'cabeza':(0xC41E,8,4,56),'mano':(0xCB2E,4,3,24)}
def frame(base,i,w,h):
    a=base+i*(2+w*h)
    hdr=(mem(a),mem(a+1))
    data=[mem(a+2+k) for k in range(w*h)]
    return hdr,data
def bmp(data,w,h):
    im=Image.new('L',(w*8,h),0); p=im.load()
    for y in range(h):
        for bx in range(w):
            v=data[y*w+bx]
            for k in range(8): p[bx*8+k,y]=255 if v&(0x80>>k) else 0
    return im
if __name__=='__main__':
    for name,(base,n,w,h) in OBJS.items():
        ims=[]
        for i in range(n):
            hdr,data=frame(base,i,w,h); print(name,i,'cabecera',hdr); ims.append(bmp(data,w,h))
        sc=8 if name!='cabeza' else 6
        sheet=Image.new('L',((w*8*sc+10)*n,h*sc),90)
        for i,im in enumerate(ims): sheet.paste(im.resize((w*8*sc,h*sc),Image.NEAREST),(i*(w*8*sc+10),0))
        sheet.save('fr_%s.png'%name)
