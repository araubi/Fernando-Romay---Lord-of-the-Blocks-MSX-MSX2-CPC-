import sys
from colorize import *
from PIL import Image, ImageDraw
CL={'S':(255,182,109),'C':(255,36,36),'P':(36,36,218),'M':(255,255,255),'Z':(200,200,200),'B':(255,255,0),'#':(0,0,0),'.':(40,40,90)}
def render(ids, fn, cls_fn=classify):
    S=12; W=24*S+30
    sheet=Image.new('RGB',(W*len(ids),40*S+30),(60,60,60)); d=ImageDraw.Draw(sheet)
    for k,i in enumerate(ids):
        rows=cls_fn(i); X=k*W+20; Y=20
        d.text((X,2),'%02X'%i,fill=(255,255,0))
        for y,l in enumerate(rows):
            d.text((X-18,Y+y*S),str(y),fill=(200,200,200))
            for x,ch in enumerate(l):
                d.rectangle([X+x*S,Y+y*S,X+x*S+S-2,Y+y*S+S-2],fill=CL[ch])
        for x in range(0,24,4): d.text((X+x*S,Y+len(rows)*S),str(x),fill=(200,200,200))
    sheet.save(fn)
if __name__=='__main__':
    render([int(a,16) for a in sys.argv[2:]], sys.argv[1])
