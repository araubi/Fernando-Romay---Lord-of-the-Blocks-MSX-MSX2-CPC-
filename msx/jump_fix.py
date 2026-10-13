"""Retoques a mano/por reglas de los saltos (despues de dunk_patch): Romay (30,31,32,36,37,38,39)
pelo abultado + nariz; Iturriaga barba y menton en (34,35,3C,3D)."""
from romay_patch import read_f2, bulk_hair
from heads import encode_head
from sprites import entry
# orientacion de la cara de Romay en cada fotograma (lado de la nariz) y filas de la nariz
ROMAY = {0x30:('L',range(9,12)),0x31:('L',range(9,12)),0x32:('R',range(9,11)),0x36:('L',range(8,10)),
         0x37:('L',range(8,10)),0x38:None,0x39:None}
def grow(rows, top, back, times=2):
    for _ in range(times): rows=bulk_hair(rows, top)
    return rows
def nose(rows, side, rr):
    g=[list(l) for l in rows]
    for y in rr:
        line=rows[y]
        xs=[x for x,ch in enumerate(line) if ch!='.']
        if not xs: continue
        if side=='L':
            x0=xs[0]                      # contorno delantero
            if x0>=1 and line[x0]=='#': g[y][x0]='o'; g[y][x0-1]='#'
        else:
            x0=xs[-1]
            if x0<=22 and line[x0]=='#': g[y][x0]='o'; g[y][x0+1]='#'
    return [''.join(l) for l in g]
def setpix(rows, pts, ch):
    g=[list(l) for l in rows]
    for x,y in pts: g[y][x]=ch
    return [''.join(l) for l in g]
# zonas (x0,x1,y0,y1) donde puede crecer el pelo de Romay en cada fotograma, y filas de pelo de origen
GROW = {0x30:([(5,19,1,4),(14,20,4,10)],10), 0x31:([(14,20,3,11)],11), 0x32:([(3,8,3,11),(8,16,2,4)],11),
        0x36:([(4,12,0,3)],9), 0x37:([(4,15,0,3),(15,19,3,11)],11), 0x38:([(5,15,0,3),(3,7,2,9)],12),
        0x39:([(5,17,0,3),(3,7,3,9),(17,20,3,10)],12)}
def grow_box(rows, boxes, hb, times=2):
    for _ in range(times):
        g=[list(l) for l in rows]
        for x0,x1,y0,y1 in boxes:
            for y in range(y0,y1+1):
                for x in range(x0,x1+1):
                    if rows[y][x]!='.': continue
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        X,Y=x+dx,y+dy
                        if 0<=X<24 and 0<=Y<=hb and rows[Y][X]=='#': g[y][x]='#'; break
        rows=[''.join(l) for l in g]
    return rows
def fixed(F2):
    out={}
    for i,cfg in ROMAY.items():
        r=read_f2(F2,i)
        boxes,hb=GROW[i]; r=grow_box(r,boxes,hb,2)
        if cfg: r=nose(r,*cfg)
        out[i]=r
    # Iturriaga de espaldas: barba en la mandibula visible y menton recortado
    for i in (0x3C,0x3D):
        r=read_f2(F2,i)
        pts=[(x,y) for y in range(10,13) for x in range(13,19) if r[y][x]=='o']
        r=setpix(r,pts,'#')
        out[i]=r
    # Iturriaga brazo arriba (34,35): barba limpia en la parte baja de la cara
    r=read_f2(F2,0x34)
    r=setpix(r,[(x,y) for y in range(12,16) for x in range(7,10) if r[y][x]=='o'],'#')
    out[0x34]=r
    r=read_f2(F2,0x35)
    r=setpix(r,[(x,y) for y in range(12,16) for x in range(8,12) if r[y][x]=='o'],'#')
    out[0x35]=r
    return out
def apply(F1,F2,F3):
    for i,rows in fixed(F2).items():
        a=entry(i)+2-0x415A; d=encode_head(rows); F2[a:a+len(d)]=d

NECK=13
def raise_head(rows, k=2, n=NECK):
    H=len(rows)
    t=0
    while t<k and not rows[t].strip('.'): t+=1
    b=0
    while t+b<k and not rows[H-1-b].strip('.'): b+=1
    c=k-t-b
    head=rows[:n+1]; body=rows[n+1:]
    new=head[t+c:]+[rows[n]]*k+body[:len(body)-b]
    assert len(new)==H
    return new,(t,b,c)
_fixed_old=fixed
def fixed(F2, log=None):
    out=_fixed_old(F2)
    for i in ROMAY:
        out[i],info=raise_head(out[i])
        if log is not None: log.append((i,info))
    return out
def apply(F1,F2,F3):
    for i,rows in fixed(F2).items():
        a=entry(i)+2-0x415A; d=encode_head(rows); F2[a:a+len(d)]=d
