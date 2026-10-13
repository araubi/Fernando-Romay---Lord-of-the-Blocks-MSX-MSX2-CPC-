"""Clasificacion de los pixeles de relleno de cada fotograma de jugador en zonas:
S piel, C camiseta, P pantalon, M medias, Z zapatillas, B balon. '#' tinta, '.' transparente."""
import pickle
from collections import deque
F=pickle.load(open('/home/claude/w/frames_final.pkl','rb'))
HEADS={0x0A,0x0B,0x16,0x17,0x22,0x23,0x2E,0x2F}
JUMP=set(range(0x30,0x3E))
def comps(rows):
    h,w=len(rows),len(rows[0]); lab=[[-1]*w for _ in range(h)]; out=[]
    for y in range(h):
        for x in range(w):
            if rows[y][x]=='o' and lab[y][x]<0:
                q=deque([(x,y)]); lab[y][x]=len(out); pts=[]
                while q:
                    cx,cy=q.popleft(); pts.append((cx,cy))
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        X,Y=cx+dx,cy+dy
                        if 0<=X<w and 0<=Y<h and rows[Y][X]=='o' and lab[Y][X]<0:
                            lab[Y][X]=len(out); q.append((X,Y))
                out.append(pts)
    return out,lab

def checker(rows,x,y):
    h,w=len(rows),len(rows[0]); n=0
    for dx,dy in ((1,1),(-1,1),(1,-1),(-1,-1)):
        X,Y=x+dx,y+dy
        if 0<=X<w and 0<=Y<h and rows[Y][X]=='o': n+=1
    m=0
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        X,Y=x+dx,y+dy
        if 0<=X<w and 0<=Y<h and rows[Y][X]=='#': m+=1
    return n>=2 and m>=3

def interior(pts):
    P=set(pts); return sum(1 for x,y in pts if all((x+dx,y+dy) in P for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))))

def classify(i):
    rows=F[i]; h=len(rows); cs,lab=comps(rows)
    cls=[['#' if ch=='#' else ('.' if ch=='.' else 'S') for ch in l] for l in rows]
    if i in HEADS: return [''.join(l) for l in cls]
    y0=12 if i in JUMP else 0
    H=h-y0
    info=[]
    for k,pts in enumerate(cs):
        ys=[p[1] for p in pts]; xs=[p[0] for p in pts]
        info.append(dict(k=k,n=len(pts),top=min(ys),bot=max(ys),cy=sum(ys)/len(ys),cx=sum(xs)/len(xs),pts=pts,
                         w=max(xs)-min(xs)+1,I=interior(pts)))
    kind={}
    for c in info:
        if c['n']<=2 and all(checker(rows,x,y) for x,y in c['pts']): kind[c['k']]='B'
    body=[c for c in info if c['k'] not in kind and c['cy']>=y0+1]
    cand=[c for c in body if c['cy']<=y0+H*0.55]
    torso=max(cand,key=lambda c:(c['I'],c['n'])) if cand else None
    if torso and torso['I']>=2:
        kind[torso['k']]='C'
        tb=torso['bot']
        sh=[c for c in body if c['k'] not in kind and tb-3<=c['top']<=tb+3 and c['cy']<=tb+H*0.22
            and (c['I']>=2 or (c['n']>=6 and c['w']>=4)) and abs(c['cx']-torso['cx'])<=6
            and c['bot']-c['top']<=H*0.3]
        for c in sh: kind[c['k']]='P'
    for c in body:
        if c['k'] in kind: continue
        if c['bot']>=h-3 and c['top']>=h-8: kind[c['k']]='Z'
        elif c['top']>=h-11 and c['bot']>=h-6 and c['n']<=16: kind[c['k']]='M'
    for c in info:
        t=kind.get(c['k'],'S')
        for x,y in c['pts']: cls[y][x]=t
    return [''.join(l) for l in cls]

# correcciones manuales: ('seed',x,y,clase) rellena la zona; ('rect',x0,y0,x1,y1,de,a) cambia una clase en un rectangulo
OVR={
 0x01:[('seed',6,13,'S')],
 0x0D:[('seed',17,13,'S')],
 0x02:[('rect',0,15,23,20,'C','P'),('rect',0,19,23,25,'P','S'),('rect',9,12,15,15,'S','C')],
 0x0E:[('rect',0,15,23,20,'C','P'),('rect',0,19,23,25,'P','S'),('rect',8,12,14,15,'S','C')],
 0x11:[('rect',0,15,23,20,'C','P'),('rect',0,19,23,25,'P','S'),('rect',8,12,14,15,'S','C')],
 0x05:[('rect',0,15,23,20,'C','P'),('rect',0,19,23,25,'P','S'),('rect',8,13,14,15,'S','C')],
 0x2D:[('rect',0,0,23,13,'C','S'),('rect',0,14,23,20,'P','C'),('rect',5,21,16,23,'S','P')],
 0x08:[('rect',0,0,23,13,'C','S')], 0x09:[('rect',0,0,23,13,'C','S')],
 0x14:[('rect',0,0,23,13,'C','S')], 0x15:[('rect',0,0,23,13,'C','S')],
 0x36:[('rect',0,0,23,15,'C','S')], 0x37:[('rect',0,0,23,15,'C','S')],
}
_classify_auto=classify
def classify(i):
    rows=[list(l) for l in _classify_auto(i)]
    for op in OVR.get(i,[]):
        if op[0]=='seed':
            _,x,y,t=op; src=rows[y][x]; st=[(x,y)]
            while st:
                cx,cy=st.pop()
                if 0<=cy<len(rows) and 0<=cx<24 and rows[cy][cx]==src and F[i][cy][cx]=='o':
                    rows[cy][cx]=t; st+= [(cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)]
        else:
            _,x0,y0,x1,y1,a,b=op
            for y in range(y0,min(y1+1,len(rows))):
                for x in range(x0,x1+1):
                    if rows[y][x]==a: rows[y][x]=b
    return [''.join(l) for l in rows]
