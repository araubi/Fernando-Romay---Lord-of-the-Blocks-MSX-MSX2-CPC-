import build, frames, p_jordan
from PIL import Image, ImageDraw, ImageFont
im=build.make(); m=bytes(im.mem())
C=frames.cpc_frames(m,n=75)
def jhead(e):
    hd=p_jordan.head_data(e); rows=[]
    for y in range(16):
        r=[]
        for b in hd[2+4*y:6+4*y]:
            for q in range(4): r.append(((b>>(7-q))&1)|(((b>>(3-q))&1)<<1))
        rows.append(r)
    return rows
heads={0x0A,0x0B,0x16,0x17,0x22,0x23,0x2E,0x2F}
body=[i for i in range(0,48) if i not in heads]
jumps=[0x30,0x31,0x32,0x36,0x37,0x38,0x39]
items=[('cabeza %02X'%e, jhead(e)) for e in (0x0A,0x16,0x22,0x2E)]
items+=[('cuerpo %02X'%i, C[i][1]) for i in body]
items+=[('salto %02X'%i, C[i][1]) for i in jumps]
PAL={0:(40,60,200),1:(0,0,0),2:(255,255,255),3:(0,0,0)}
S=8; cw=24*S+16; ch=40*S+30; cols=6
W=Image.new('RGB',(cols*cw, ((len(items)+cols-1)//cols)*ch),(70,70,70)); d=ImageDraw.Draw(W)
for k,(name,rows) in enumerate(items):
    ox=(k%cols)*cw+8; oy=(k//cols)*ch+22
    d.text((ox,oy-18),name,fill=(255,255,0))
    for y,r in enumerate(rows):
        for x,p in enumerate(r):
            d.rectangle([ox+x*S,oy+y*S,ox+x*S+S-2,oy+y*S+S-2],fill=PAL[p])
W.save('/mnt/user-data/outputs/CPC_Jordan_graficos.png'); print(W.size, len(items))
