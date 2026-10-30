from PIL import Image
def players(s, path, sc=4):
    m=s.m; im=s.img()
    out=[]
    for base in (0x112F,0x1149):
        l=m.ram[base+2]; h=m.ram[base+3]
        x=(32+2*h)*2; y=24+l-40
        box=(max(0,x-60),max(0,y-10),max(0,x-60)+140,max(0,y-10)+70)
        out.append(im.crop(box).resize((140*sc//2*1,70*sc),Image.NEAREST))
    W=Image.new('RGB',(sum(o.width for o in out)+10,out[0].height),(80,80,80)); x=0
    for o in out: W.paste(o,(x,0)); x+=o.width+10
    W.save(path)
