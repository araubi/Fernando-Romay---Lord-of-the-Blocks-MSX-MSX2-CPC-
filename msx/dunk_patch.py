"""Saltos/tiros/mates (sprites 30-3D): la cabeza va incrustada. Se aplica la barba a los fotogramas
del pelo corto (30-32, 36-37) y se intercambian con sus espejos del otro lado."""
from sprites import entry, p1
from heads import get_head, encode_head
import beard_patch
from jumpheads import grid
PAIRS=[(0x30,0x33),(0x31,0x34),(0x32,0x35),(0x36,0x3A),(0x37,0x3B),(0x38,0x3C),(0x39,0x3D)]
PROFILE=[0x30,0x31,0x32,0x36,0x37]
def beard_diff():
    old=get_head(0x0A); new=beard_patch.heads()[0x0A]
    return [(x,y,old[y][x],new[y][x]) for y in range(16) for x in range(24) if old[y][x]!=new[y][x]], old
def align(g, old):
    best=None
    for dy in range(-4,5):
        for dx in range(-4,5):
            s=0
            for y in range(3,15):
                for x in range(24):
                    Y,X=y+dy,x+dx
                    if old[y][x]!='.' and 0<=Y<len(g) and 0<=X<24 and g[Y][X]==old[y][x]: s+=1
            if best is None or s>best[0]: best=(s,dx,dy)
    return best
def bearded(i, log=None):
    g=[list(l) for l in grid(i)]; diff,old=beard_diff()
    s,dx,dy=align(g,old); n=0
    for x,y,o,nw in diff:
        X,Y=x+dx,y+dy
        if 0<=Y<len(g) and 0<=X<24 and g[Y][X]==o:
            g[Y][X]=nw; n+=1
    if log is not None: log.append((i,dx,dy,n,len(diff)))
    return [''.join(l) for l in g]
def apply(F1,F2,F3, log=None):
    src={i:grid(i) for p in PAIRS for i in p}
    for i in PROFILE: src[i]=bearded(i,log)
    for a,b in PAIRS:
        na=[l[::-1] for l in src[b]]; nb=[l[::-1] for l in src[a]]
        for i,rows in ((a,na),(b,nb)):
            off=entry(i)+2-0x415A
            data=encode_head(rows)
            assert len(data)==len(rows)*6
            F2[off:off+len(data)]=data
if __name__=='__main__':
    log=[]; F2=bytearray(0x10000)
    import common
    _,_,F=common.files(); F2=bytearray(F['f2'][3])
    apply(None,F2,None,log)
    for l in log: print('sprite %02X desplazamiento (%d,%d) pixeles de barba aplicados %d/%d'%l)
