import glob
from PIL import Image
CAS=glob.glob('/mnt/user-data/uploads/*Software*.cas')[0]
H=bytes([0x1F,0xA6,0xDE,0xBA,0xCC,0x13,0x7D,0x74])
def cas_blocks(data):
    pos=[];i=0
    while (i:=data.find(H,i))>=0: pos.append(i);i+=8
    return pos,[data[pos[k]+8:(pos[k+1] if k+1<len(pos) else len(data))] for k in range(len(pos))]
def files():
    d=open(CAS,'rb').read(); pos,segs=cas_blocks(d); F={}
    for n,ci in (('f1',3),('f2',5),('f3',7)):
        c=segs[ci];s=c[0]|c[1]<<8;e=c[2]|c[3]<<8;x=c[4]|c[5]<<8
        F[n]=(s,e,x,c[6:6+e-s+1])
    return d,pos,F
PAL=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
def decode(b):
    pat=b[:0x1800]; small=b[0x1800:0x1B00]
    px=[[0]*256 for _ in range(192)]
    for t in range(768):
        ty,tx=divmod(t,32); c=small[t]; fg,bg=c>>4,c&15
        for r in range(8):
            p=pat[t*8+r]
            for k in range(8): px[ty*8+r][tx*8+k]=fg if p&(0x80>>k) else bg
    return px
def to_img(px):
    im=Image.new('RGB',(256,192)); q=im.load()
    for y in range(192):
        for x in range(256): q[x,y]=PAL[px[y][x]]
    return im
def encode(px,orig):
    """reconstruye patrones; color por tile (tiles de 8x8 con color unico, como el original)"""
    import collections
    pat=bytearray(orig[:0x1800]); col=bytearray(orig[0x1800:0x1B00]); bad=[]
    for t in range(768):
        ty,tx=divmod(t,32)
        cells=[[px[ty*8+r][tx*8+k] for k in range(8)] for r in range(8)]
        cn=collections.Counter(c for row in cells for c in row)
        cs=[c for c,_ in cn.most_common()]
        if len(cs)>2: bad.append((tx,ty,cs))
        oc=orig[0x1800+t]; ofg,obg=oc>>4,oc&15
        if set(cs)<= {ofg,obg}: fg,bg=ofg,obg
        else:
            bg=1 if 1 in cs else cs[0]
            others=[c for c in cs if c!=bg]; fg=others[0] if others else ofg
        col[t]=fg<<4|bg
        for r in range(8):
            v=0
            for k in range(8):
                if cells[r][k]!=bg: v|=0x80>>k
            pat[t*8+r]=v
    return bytes(pat)+bytes(col),bad
