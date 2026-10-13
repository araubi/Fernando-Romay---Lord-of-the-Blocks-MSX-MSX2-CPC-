"""Aplica todas las modificaciones sobre el CAS original y devuelve los bytes del CAS nuevo."""
import numpy as np
from common import *
import head5
SL=0.5
def logo_nidamic(px):
    pts=[(x,y) for y in range(72,90) for x in range(140,190) if px[y][x]==7]
    xp=lambda x,y:int(round(x-SL*(86-y)))
    def letter(x,y):
        v=xp(x,y); return 'D' if v<=156 else ('I' if v<=162 else ('N' if v<=176 else None))
    G={'D':[],'I':[],'N':[]}
    for x,y in pts:
        l=letter(x,y)
        if l: G[l].append((x,y))
    ext={k:(min(xp(x,y) for x,y in v),max(xp(x,y) for x,y in v)) for k,v in G.items()}
    g1=ext['I'][0]-ext['D'][1]; g2=ext['N'][0]-ext['I'][1]
    pos={}; cur=ext['D'][0]
    for k in ('N','I','D'):
        pos[k]=cur; cur+=ext[k][1]-ext[k][0]+(g1 if k=='N' else g2)
    for v in G.values():
        for x,y in v: px[y][x]=1
    for l,v in G.items():
        dd=pos[l]-ext[l][0]
        for x,y in v: px[y][x+dd]=7
SIX=["...#####.",
     ".##....#.",
     "##.......",
     "##.####..",
     "###....#.",
     "##.....##",
     "##.....##",
     ".##...##.",
     "..#####..",
     "........."]
def shirt_six(px):
    for y in range(78,86):
        for x in range(51,64): px[y][x]=15
    for y in range(81,86):            # resto de la curva de la D en x=64
        if px[y][64]==1 and px[y][65]==15: px[y][64]=15
    for y in range(86,89):
        for x in range(51,64): px[y][x]=15     # incluye la esquina inferior derecha de la D
    px[82][64]=15                              # pixel suelto de la curva de la D
    for x,y in ((64,81),(64,82),(64,83),(63,84),(63,85)): px[y][x]=1   # contorno de los dedos (retoque del usuario)
    for r,row in enumerate(SIX):
        for k,ch in enumerate(row):
            if ch=='#': px[78+r][52+k]=1
HEAD_BASE,HAND_BASE=0xC41E,0xCB2E
def put_bitmap(f3,base,i,w,h,bits):
    a=base+i*(2+w*h)+2-0x84D0
    for y in range(h):
        for bx in range(w):
            v=0
            for k in range(8):
                if bits[y][bx*8+k]: v|=0x80>>k
            f3[a+y*w+bx]=v
def get_bitmap(f3,base,i,w,h):
    a=base+i*(2+w*h)+2-0x84D0
    return [[bool(f3[a+y*w+x//8]&(0x80>>(x%8))) for x in range(w*8)] for y in range(h)]
def presentation(F1,F3):
    px=decode(bytes(F1[:0x1B00]))
    logo_nidamic(px); shirt_six(px)
    for y in range(19,28): px[y][80]=1
    h0=head5.build(0)
    for y in range(56):
        for x in range(32): px[8+y][48+x]=15 if h0[y,x] else 1
    img,bad=encode(px,bytes(F1[:0x1B00])); assert not bad, bad
    F1[:0x1B00]=img
    for i in range(8): put_bitmap(F3,HEAD_BASE,i,4,56,head5.build(i))
    for i in range(4):
        bm=get_bitmap(F3,HAND_BASE,i,3,24)
        for r in range(9):
            for c in range(8):
                if r<=5 or c<=7: bm[r][c]= px[80+r][56+c]==15
            for r in range(6):
                bm[r][8]= px[80+r][64]==15
        put_bitmap(F3,HAND_BASE,i,3,24,bm)
    return px
EXTRA=[]   # otros parches (menu, nombres, lados): funciones f(F1,F2,F3)
def build(orig=None):
    d=bytearray(orig or open(CAS,'rb').read())
    pos,segs=cas_blocks(bytes(d))
    off={k:pos[ci]+8+6 for k,ci in (('f1',3),('f2',5),('f3',7))}
    _,_,F=files()
    F1=bytearray(F['f1'][3]); F2=bytearray(F['f2'][3]); F3=bytearray(F['f3'][3])
    presentation(F1,F3)
    for f in EXTRA: f(F1,F2,F3)
    for k,arr in (('f1',F1),('f2',F2),('f3',F3)):
        d[off[k]:off[k]+len(arr)]=arr
    return bytes(d)
if __name__=='__main__':
    out=build(); open('nidamic.cas','wb').write(out)
    print('CAS',len(out))
