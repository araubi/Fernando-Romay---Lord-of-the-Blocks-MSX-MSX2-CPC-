"""Paleta y colores de los jugadores para MSX2 (SCREEN 4 + sprites modo 2)."""
from colorize import F, classify, HEADS
# paleta MSX2 (R,G,B en 0-7). Se reprograman indices que el juego no usa: 2, 3, 13
PAL2={1:(0,0,0),2:(7,1,1),3:(1,2,6),13:(7,5,3),15:(7,7,7)}
NAMES={2:'rojo',3:'azul',13:'piel',15:'blanco'}
ITU={'S':13,'C':2,'P':3,'M':15,'Z':15,'B':15}
ROM={'S':13,'C':15,'P':15,'M':15,'Z':15,'B':15}
# fotogramas de cada jugador (estado normal: ITU a la izquierda)
BODIES=[i for i in range(0x2E) if i not in HEADS]
ITU_FR=BODIES+[0x0B,0x17,0x23,0x2F]+[0x33,0x34,0x35,0x3A,0x3B,0x3C,0x3D]
ROM_FR=BODIES+[0x0A,0x16,0x22,0x2E]+[0x30,0x31,0x32,0x36,0x37,0x38,0x39]
def rgb(i): r,g,b=PAL2[i]; return (r*255//7,g*255//7,b*255//7)
def colored(i,M):
    return [[('#' if ch=='#' else ('.' if ch=='.' else M[ch])) for ch in l] for l in classify(i)]
def feasible(cols):
    cols=set(cols)
    if len(cols)<=2: return (sorted(cols)+[0,0])[:2]
    for a in (2,3,13,15):
        for b in (2,3,13,15):
            if a<b and cols<= {a,b,a|b}: return (a,b)
    return None
def check(frames,M):
    bad=[]
    for i in frames:
        for y,row in enumerate(colored(i,M)):
            cs=[c for c in row if isinstance(c,int)]
            if cs and feasible(cs) is None: bad.append((i,y,sorted(set(cs))))
    return bad
if __name__=='__main__':
    for n,fr,M in (('ITU',ITU_FR,ITU),('ROMAY',ROM_FR,ROM)):
        b=check(fr,M); print(n,'filas imposibles:',len(b), b[:20])

def resolved(i,M):
    """colores por pixel ajustados a lo que permiten 2 capas + OR en cada fila"""
    rows=colored(i,M)
    for y,row in enumerate(rows):
        cs=[c for c in row if isinstance(c,int)]
        if not cs or feasible(cs): continue
        from collections import Counter
        cnt=Counter(cs); best=None
        for victim in cnt:
            for repl in cnt:
                if repl==victim: continue
                new=[repl if c==victim else c for c in cs]
                if feasible(new) and (best is None or cnt[victim]<best[0]): best=(cnt[victim],victim,repl)
        _,v,r=best
        rows[y]=[r if c==v else c for c in row]
    return rows
