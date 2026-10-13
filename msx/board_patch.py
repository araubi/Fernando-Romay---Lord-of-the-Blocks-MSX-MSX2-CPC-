"""Valla publicitaria: Mirinda | MSX | ASTRAN PCP (filas 41-55 del bitmap de la pista)."""
import numpy as np
from court import court_bits, put_bits
G={
'A':""" ..###..|.##.##.|##...##|##...##|##...##|#######|#######|##...##|##...##|##...##|##...##""",
'S':""" .#####.|##...##|##.....|###....|.#####.|..#####|....###|.....##|.....##|##...##|.#####.""",
'T':""" ######|######|..##..|..##..|..##..|..##..|..##..|..##..|..##..|..##..|..##..""",
'R':""" ######.|##...##|##...##|##...##|######.|####...|##.##..|##..##.|##..##.|##...##|##...##""",
'N':""" ##...##|##...##|###..##|###..##|####.##|##.####|##..###|##..###|##...##|##...##|##...##""",
'P':""" ######.|##...##|##...##|##...##|##...##|######.|##.....|##.....|##.....|##.....|##.....""",
'C':""" .#####.|##...##|##.....|##.....|##.....|##.....|##.....|##.....|##.....|##...##|.#####.""",
'M':""" ##.....##|###...###|####.####|##.###.##|##..#..##|##.....##|##.....##|##.....##|##.....##|##.....##|##.....##""",
'i':""" ##|##|..|..|##|##|##|##|##|##|##""",
'r':""" .....|.....|.....|.....|##.##|#####|###..|##...|##...|##...|##...""",
'n':""" ......|......|......|......|##.##.|######|##..##|##..##|##..##|##..##|##..##""",
'd':""" ....##|....##|....##|....##|.#####|##..##|##..##|##..##|##..##|##..##|.#####""",
'a':""" ......|......|......|......|.####.|....##|.#####|##..##|##..##|##..##|.#####""",
}
def glyph(ch): return [r for r in G[ch].strip().split('|')]
def text_bits(s, gap=1, space=4):
    cols=[]
    for ch in s:
        if ch==' ': cols+=[[0]*11]*space; continue
        g=glyph(ch); w=len(g[0])
        for x in range(w): cols.append([g[y][x]=='#' for y in range(11)])
        cols+=[[0]*11]*gap
    cols=cols[:-gap]
    return np.array(cols,bool).T
Y0,Y1=41,55
def draw(b):
    b=b.copy(); o=court_bits.__globals__  # noqa
    msx=b[Y0:Y1+1,82:130].copy()
    # borde derecho de la valla en cada fila
    for y in range(Y0,Y1+1):
        b[y,32:225]=False
    b[Y0:Y1+1,94:96]=True
    b[Y0:Y1+1,96:144]=msx
    t=text_bits('Mirinda'); w=t.shape[1]; x=32+(94-32-w)//2; b[43:54,x:x+w]|=t
    t=text_bits('ASTRAN PCP'); w=t.shape[1]
    right=224
    x=144+(right-144-w+1)//2; b[43:54,x:x+w]|=t
    return b
def apply(F1,F2,F3):
    put_bits(F3,draw(court_bits(F3)))
if __name__=='__main__':
    from PIL import Image
    import pickle
    vr,ram=pickle.load(open('state460.pkl','rb'))
    base=np.unpackbits(np.frombuffer(ram[0xB498:0xB498+32*112],np.uint8)).reshape(112,256).astype(bool)
    nb=draw(base)
    for y in range(38,58): print(''.join('#' if v else '.' for v in nb[y,24:232]))
