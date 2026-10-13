"""Datos de color de los jugadores para la ROM MSX2.
Capas por personaje (indices de paleta):
  ITU  : B = piel (12) ; A = ropa por fila (rojo 2 / azul 6 / blanco 15) ; A+B = naranja (14)
  ROMAY: B = piel (3)  ; A = naranja (14) ; A+B = blanco (15)
Bloque por (personaje, fotograma, desplazamiento 0-3): h bytes de color de fila + h*8 bytes
(A[4], B[4]); lo opaco se calcula como A|B ya desplazados 2*s pixeles. Indice: 4 bytes (banco, dir lo, dir hi, h)."""
import pickle
from colorize import F
D=pickle.load(open('/home/claude/w/msx2_classes.pkl','rb'))
PAIRS={0x0A:0x0B,0x16:0x17,0x22:0x23,0x2E:0x2F,0x30:0x33,0x31:0x34,0x32:0x35,0x36:0x3A,0x37:0x3B,0x38:0x3C,0x39:0x3D}
PAIRS.update({v:k for k,v in list(PAIRS.items())})
HEADS={0x0A,0x0B,0x16,0x17,0x22,0x23,0x2E,0x2F}
JUMPS=set(range(0x30,0x3E))
PAL={2:(7,1,1),3:(7,5,3),6:(1,2,6),12:(7,5,3),14:(7,3,1)}     # indices reprogramados en partido
BCOL={0:12,1:3}
def mirror(rows):
    return [r[::-1] for r in rows]
def classes(c, i):
    """clases del contenido del fotograma i cuando lo usa el personaje c (0 ITU, 1 ROMAY)"""
    key='itu' if c==0 else 'romay'
    own=D[key]
    if i in own: return own[i]
    p=PAIRS[i]                                   # fotograma del otro lado: contenido del compañero
    return own[p] if i in HEADS else mirror(own[p])
def rowdata(c, rows):
    """-> lista por fila: (color A, opaco24, A24, B24), con conflictos resueltos"""
    out=[]; conflicts=0
    for r in rows:
        O=A=B=0; col=0
        cloth=[ch for ch in r if ch in 'RLW'] if c==0 else []
        if c==0 and cloth:
            from collections import Counter
            col={'R':2,'L':6,'W':15}[Counter(cloth).most_common(1)[0][0]]
            if len(set(cloth))>1: conflicts+=1
        # ITU: fila con balon naranja y blanco (zapatillas/medias) y sin piel -> capa B en naranja
        bover=0
        if c==0 and 'O' in r and 'W' in cloth and 'S' not in r:
            bover=14; col=15
            if len(set(cloth))>1: conflicts-=1          # no es conflicto: se resuelve con la capa B
        elif c==0 and 'O' in r and not cloth:
            col=2                                       # rojo|piel = naranja
        for x,ch in enumerate(r):
            bit=1<<(23-x)
            if ch!='.': O|=bit
            if ch in '#.': continue
            if c==0:
                if ch=='S': B|=bit
                elif ch=='O':
                    if bover: B|=bit
                    else: A|=bit; B|=bit
                elif ch=='W' and bover: A|=bit
                else: A|=bit
            else:
                if ch=='S': B|=bit
                elif ch=='O': A|=bit
                else: A|=bit; B|=bit                 # blanco
        if c==1: col=14
        if not A: col=0
        out.append((col|(bover<<4),O,A,B))
    return out, conflicts
def shifted(v, s):
    v32=(v<<8)>>(2*s)
    return [(v32>>24)&255,(v32>>16)&255,(v32>>8)&255,v32&255]
def block(c, i, s):
    rows=classes(c,i); rd,_=rowdata(c,rows); h=len(rows)
    out=bytearray(r[0] for r in rd)
    for col,O,A,B in rd:
        a,b=shifted(A,s),shifted(B,s)
        nz=[k for k in range(4) if a[k]|b[k]]
        hdr=(nz[0]|(nz[-1]<<4)) if nz else 0xFF          # primera | ultima columna con datos
        out+=bytes([hdr])+bytes(x for p in zip(a,b) for x in p)      # hdr A0 B0 A1 B1 A2 B2 A3 B3
    return bytes(out), h
FRAMES=[i for i in range(0x3E)]
def build(first_bank=4, nbanks=12):
    """-> dict banco->bytes (16 KB) ; el indice va al principio del primer banco"""
    banks={b:bytearray(0x4000) for b in range(first_bank,first_bank+nbanks)}
    idx=bytearray(2*64*4*4)
    cur_b=first_bank; cur=len(idx)
    for c in (0,1):
        for i in FRAMES:
            for s in range(4):
                data,h=block(c,i,s)
                if cur+len(data)>0x4000: cur_b+=1; cur=0
                assert cur_b<first_bank+nbanks, 'sin espacio'
                banks[cur_b][cur:cur+len(data)]=data
                e=((c*64+i)*4+s)*4; a=0x4000+cur
                idx[e:e+4]=bytes([cur_b,a&255,a>>8,h])
                cur+=len(data)
    banks[first_bank][0:len(idx)]=idx
    return banks, cur_b
if __name__=='__main__':
    tot=0
    for c in (0,1):
        n=0
        for i in FRAMES:
            _,k=rowdata(c,classes(c,i)); n+=k
        print('personaje',c,'filas con dos colores de ropa (resueltas por mayoria):',n)
    banks,last=build()
    print('bancos usados hasta',last)
