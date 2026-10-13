from sprites import *
def sprite2(i):
    a=entry(i); h=p1(a); w=p1(a+1); a+=2
    return h,w,[[p1(a+y*w+k) for k in range(w)] for y in range(h)]
def render2(i,mode,sc=6):
    h,w,rows=sprite2(i)
    npx=(w//2)*8
    im=Image.new('RGB',(npx,h),(0,160,160)); p=im.load()
    for y,r in enumerate(rows):
        for bx in range(w//2):
            if mode==0: m,dd=r[2*bx],r[2*bx+1]
            elif mode==1: dd,m=r[2*bx],r[2*bx+1]
            elif mode==2: dd,m=r[bx],r[bx+w//2]
            else: m,dd=r[bx],r[bx+w//2]
            for k in range(8):
                mb=m&(0x80>>k); db=dd&(0x80>>k)
                p[bx*8+k,y]=(255,255,255) if db else ((0,160,160) if mb else (0,0,0))
    return im.resize((npx*sc,h*sc),Image.NEAREST)
idxs=[0x0A,0x0B,0x09,0x15]
rows=[]
for mode in range(4):
    ims=[render2(i,mode) for i in idxs]
    rows.append(ims)
W=sum(im.width+6 for im in rows[0]); H=sum(max(im.height for im in r)+6 for r in rows)
s=Image.new('RGB',(W,H),(60,60,60)); y=0
for r in rows:
    x=0
    for im in r: s.paste(im,(x,y)); x+=im.width+6
    y+=max(im.height for im in r)+6
s.save('sprites2.png')
