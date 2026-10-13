"""F. ROMAY (jugador CPU): mas pelo, mas alto (cara 2 filas arriba + cuello) y nariz mas prominente."""
from heads import encode_head
from sprites import entry
from jumpheads import grid
PROFILE = [  # 0B, mirando a la izquierda; 17 es su espejo
 "..........#####.........",
 "........#########.......",
 "......############......",
 ".....##############.....",
 ".....###############....",
 "......##oooo########....",
 ".......#o##o########....",
 "......#oo#oooo######....",
 "...##oooooooooo####.....",
 "....####ooooo######.....",
 ".......###ooo######.....",
 ".......#ooooo#####......",
 ".......#ooo#o####.......",
 ".......####ooo#.........",
 "..........#ooo#.........",
 "..........#ooo#.........",
]
FRONT = [  # 23
 "........########........",
 "......############......",
 ".....##############.....",
 ".....##############.....",
 ".....######o########....",
 ".....####oooooo####.....",
 ".....###o##oo##o###.....",
 ".....###o#o#o#oo###.....",
 ".....###oo##ooo####.....",
 "......##o#oooo#.##......",
 "........#oo##oo#........",
 ".........#oooo#.........",
 ".........#oooo#.........",
 ".........#oooo#.........",
 ".........#oooo#.........",
 "..........####..........",
]
BACK = [  # 2F
 "........########........",
 "......############......",
 ".....######o#######.....",
 ".....######o#######.....",
 ".....##############.....",
 ".....##############.....",
 ".....##############.....",
 ".....##############.....",
 "......############......",
 "......############......",
 ".......##########.......",
 "........########........",
 ".........######.........",
 ".........#oooo#.........",
 ".........#oooo#.........",
 ".........#oooo#.........",
]
JUMP = [0x30,0x31,0x32,0x36,0x37,0x38,0x39]   # tras dunk_patch: fotogramas de salto de F. ROMAY
def heads():
    return {0x0B:PROFILE, 0x17:[l[::-1] for l in PROFILE], 0x23:FRONT, 0x2F:BACK}
def bulk_hair(rows, top=12):
    g=[list(l) for l in rows]; H=len(g); W=len(g[0])
    solid=lambda y,x: all(0<=y+dy<H and 0<=x+dx<W and rows[y+dy][x+dx]=='#' for dy in (-1,0,1) for dx in (-1,0,1))
    for y in range(min(top,H)):
        for x in range(W):
            if rows[y][x]!='.': continue
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    Y,X=y+dy,x+dx
                    if 0<=Y<H and 0<=X<W and solid(Y,X): g[y][x]='#'
    return [''.join(l) for l in g]
def read_f2(F2,i):
    a=entry(i)-0x415A; h=F2[a]; w=F2[a+1]; a+=2; hw=w//2; rows=[]
    for y in range(h):
        r=F2[a+y*w:a+y*w+w]; line=''
        for x in range(hw*8):
            d=r[x//8]&(0x80>>(x%8)); m=r[hw+x//8]&(0x80>>(x%8))
            line+='#' if d else ('.' if m else 'o')
        rows.append(line)
    return rows
def apply(F1,F2,F3):
    for i,rows in heads().items():
        assert len(rows)==16 and all(len(r)==24 for r in rows), i
        a=entry(i)+2-0x415A; F2[a:a+96]=encode_head(rows)
    for i in JUMP:                         # se aplica sobre el contenido ya intercambiado
        rows=bulk_hair(read_f2(F2,i))
        a=entry(i)+2-0x415A; d=encode_head(rows); F2[a:a+len(d)]=d
