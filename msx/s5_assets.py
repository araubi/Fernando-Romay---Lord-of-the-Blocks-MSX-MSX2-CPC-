"""Graficos de la version SCREEN 5 (16 colores por pixel).
- PAL: paleta del partido (RGB 0-7). Los indices 1,5,7,10,15 conservan el color de la paleta por
  defecto del MSX2 porque el marcador (que se sigue dibujando en SCREEN 2 y se convierte) los usa.
- background(): fondo 256x192 (grada, cartel, canastas y pista) a partir del montaje del usuario,
  sin los jugadores (se rellenan con el bitmap del juego y el color del vecino mas cercano).
- atlas(): fotogramas de los jugadores (51 por personaje), aros/redes, balon y sombra."""
import numpy as np, pickle
from PIL import Image

UP = '/root/.claude/uploads/4bde1580-c873-5012-b5b7-94b5463a9c6b/'
MOCK = UP + '1af7c9b5-image.png'

# ---- paleta (indice: (R,G,B) 0-7) ----
PAL = {0: (0, 0, 0), 1: (0, 0, 0), 2: (7, 5, 3), 3: (7, 6, 4), 4: (1, 2, 6), 5: (2, 3, 7), 6: (3, 6, 5),
       7: (2, 6, 7), 8: (7, 1, 1), 9: (7, 3, 1), 10: (6, 6, 1), 11: (4, 4, 4), 12: (3, 2, 1), 13: (6, 5, 3),
       14: (5, 5, 5), 15: (7, 7, 7)}
SKIN, PARQ, DBLUE, BLUE, TEAL, CYAN, RED, ORANGE, YELLOW, GREY, BROWN, PARQ2, LGREY, WHITE, BLACK = \
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 1
# paleta por defecto del MSX2 (para traducir los colores del marcador)
DEF = [(0, 0, 0), (0, 0, 0), (1, 6, 1), (3, 7, 3), (1, 1, 7), (2, 3, 7), (5, 1, 1), (2, 6, 7),
       (7, 1, 1), (7, 3, 3), (6, 6, 1), (6, 6, 4), (1, 4, 1), (6, 2, 5), (5, 5, 5), (7, 7, 7)]

def rgb8(c): return tuple(v * 255 // 7 for v in c)
def nearest(rgb, pal=PAL, skip=(0,)):
    best = None
    for i, c in pal.items():
        if i in skip: continue
        d = sum((a - b) ** 2 for a, b in zip(rgb, rgb8(c)))
        if best is None or d < best[0]: best = (d, i)
    return best[1]

def g2lut():
    """color de SCREEN 2 (paleta por defecto) -> indice de PAL"""
    lut = [0] * 16
    for i in range(1, 16):
        lut[i] = nearest(rgb8(DEF[i]), skip=(0,))
    lut[0] = 0
    return lut

def mock():
    im = Image.open(MOCK).convert('RGB')
    a = np.zeros((192, 256), np.uint8)
    for y in range(192):
        for x in range(256):
            a[y, x] = nearest(im.getpixel((x * 3 + 1, y * 3 + 1)))
    return a

# cajas de los jugadores en el montaje (x0, y0, x1, y1 inclusive)
BOXES = [(30, 54, 57, 97), (125, 54, 155, 98)]

HOOP_MASK = None     # (y, x) de pantalla tapados por algun fotograma de red (se rellena desde s5_pieces)

def background(bits, P=None):
    """bits: 112x256 (fondo del juego, filas de pantalla 8..119) -> indices 192x256.
    Dentro de las cajas de los jugadores: en la pista (y>=64) el color sale de la clasificacion del
    bitmap (court2); arriba se propaga desde los vecinos con el mismo bit."""
    import court2
    M = mock()
    out = M.copy()
    out[:8] = BLACK
    out[120:] = BLACK
    B = np.zeros((192, 256), bool); B[8:120] = bits
    known = np.ones((192, 256), bool)
    for x0, y0, x1, y1 in BOXES: known[y0:y1 + 1, x0:x1 + 1] = False
    if P is not None:                     # quitar las redes del montaje: se dibujan como piezas
        for base, (x0, y0) in HOOP_POS.items():
            for k in range(5):
                for j, row in enumerate(P.chars(base + k)):
                    for i, c in enumerate(row):
                        if c != '.': known[y0 + j, x0 + i] = False
    T = court2.classify(bits)
    cmap = {court2.PARQ: PARQ, court2.TEAL: TEAL, court2.WHITE: WHITE}
    for y in range(64, 120):
        for x in range(256):
            if not known[y, x]:
                out[y, x] = cmap[T[y - 64, x]]; known[y, x] = True
    from collections import Counter
    while not known.all():
        upd = []
        ys, xs = np.nonzero(~known)
        for y, x in zip(ys, xs):
            c = Counter()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    Y, X = y + dy, x + dx
                    if (dy or dx) and 0 <= Y < 192 and 0 <= X < 256 and known[Y, X] and B[Y, X] == B[y, x]:
                        c[out[Y, X]] += 2 if dx == 0 or dy == 0 else 1
            if c: upd.append((y, x, c.most_common(1)[0][0]))
        if not upd:
            for y, x in zip(ys, xs): out[y, x] = BLACK if B[y, x] else TEAL; known[y, x] = True
            break
        for y, x, v in upd: out[y, x] = v; known[y, x] = True
    return out

def to_img(a, scale=1):
    P = {i: rgb8(c) for i, c in PAL.items()}
    im = Image.fromarray(np.array([[P[v] for v in row] for row in a], np.uint8))
    return im.resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST) if scale > 1 else im

# ---------------------------------------------------------------------------------------------
# piezas
HOOPS = list(range(0x3E, 0x48))
BALL, SHADOW = 0x48, 0x49
HOOP_POS = {0x3E: (8, 32), 0x43: (224, 32)}          # posicion (x, y) de pantalla en el montaje
CLS = {'S': SKIN, 'R': RED, 'L': DBLUE, 'W': WHITE, 'O': ORANGE, '#': BLACK, '.': 0}

def hoop_images(P, M):
    out = {}
    for base, (x0, y0) in HOOP_POS.items():
        ref = P.chars(base)
        refcol = [[M[y0 + j, x0 + i] for i in range(len(ref[0]))] for j in range(len(ref))]
        for k in range(5):
            idx = base + k; ch = P.chars(idx)
            img = np.zeros((len(ch), len(ch[0])), np.uint8)
            for j, row in enumerate(ch):
                for i, c in enumerate(row):
                    if c == '.': continue
                    same = j < len(ref) and i < len(ref[0]) and ref[j][i] == c
                    if same: img[j, i] = refcol[j][i]
                    elif c == '#': img[j, i] = BLACK
                    else: img[j, i] = GREY
            if idx in (0x41, 0x46):                 # balon dentro de la red (filas 14-21)
                for j in range(14, len(ch)):
                    for i, c in enumerate(ch[j]):
                        if c == 'o': img[j, i] = ORANGE
                        elif c == '#': img[j, i] = BLACK
            out[idx] = img
    return out

def player_image(P, D, ch, i):
    rows = D[ch][i]; shape = P.chars(i)
    img = np.zeros((len(shape), len(shape[0])), np.uint8)
    for j, (r, s) in enumerate(zip(rows, shape)):
        for k, (c, o) in enumerate(zip(r, s)):
            if o == '.': continue
            if o == '#': img[j, k] = BLACK
            else: img[j, k] = CLS.get(c, SKIN) if c not in '#.' else SKIN
    return img

def all_pieces(P):
    """-> dict clave -> imagen (indices; 0 = transparente). clave: ('itu'|'romay', i) o ('*', i)"""
    D = pickle.load(open('/home/claude/w/msx2_classes.pkl', 'rb'))
    M = mock()
    out = {}
    for ch in ('itu', 'romay'):
        for i in sorted(D[ch]): out[(ch, i)] = player_image(P, D, ch, i)
    for idx, img in hoop_images(P, M).items(): out[('*', idx)] = img
    b = P.chars(BALL)
    out[('*', BALL)] = np.array([[{'#': BLACK, 'o': ORANGE, '.': 0}[c] for c in r] for r in b], np.uint8)
    s = P.chars(SHADOW)
    out[('*', SHADOW)] = np.array([[{'#': BROWN, 'o': BROWN, '.': 0}[c] for c in r] for r in s], np.uint8)
    out[('*', 'badge')] = np.array([[{'#': WHITE, '.': RED}[c] for c in r] for r in BADGE], np.uint8)
    return out

# insignia de la repeticion
BADGE = ['........',
         '.#####..',
         '.##..##.',
         '.##..##.',
         '.#####..',
         '.##.##..',
         '.##..##.',
         '........']

def trim(img):
    ys, xs = np.nonzero(img)
    if not len(ys): return img[:1, :2], 0, 0
    x0, x1 = xs.min(), xs.max() + 1; y0, y1 = ys.min(), ys.max() + 1
    return img[y0:y1, x0:x1], x0, y0

# zonas libres de la VRAM para el atlas (y de los comandos del VDP)
REGIONS = [(768, 128), (192, 64), (448, 64), (704, 64)]

def pack(items):
    """items: dict clave -> img recortada. Estanterias por altura. -> dict clave -> (x, y)"""
    order = sorted(items, key=lambda k: (-items[k].shape[0], -items[k].shape[1]))
    pos = {}; shelves = []          # (region, y, h, xnext)
    reg_y = [r[0] for r in REGIONS]
    for k in order:
        h, w = items[k].shape
        w2 = w + (w & 1)
        placed = False
        for sh in shelves:
            ri, y, sh_h, xn = sh
            if h <= sh_h and xn + w2 <= 256:
                pos[k] = (xn, y); sh[3] = xn + w2; placed = True; break
        if placed: continue
        for ri, (ry, rh) in enumerate(REGIONS):
            if reg_y[ri] + h <= ry + rh:
                y = reg_y[ri]; reg_y[ri] += h
                shelves.append([ri, y, h, w2]); pos[k] = (0, y); placed = True; break
        if not placed: raise ValueError('atlas lleno en %r (%dx%d)' % (k, w, h))
    return pos

def atlas_vram(P, extra=None):
    """-> (vram dict y->linea de 256 indices, tabla clave -> (sx, sy, w, h, dx, dy))"""
    ps = all_pieces(P)
    if extra: ps.update(extra)
    tr = {k: trim(v) for k, v in ps.items()}
    pos = pack({k: t[0] for k, t in tr.items()})
    canvas = {}
    tab = {}
    for k, (x, y) in pos.items():
        img, dx, dy = tr[k]; h, w = img.shape
        for j in range(h):
            line = canvas.setdefault(y + j, np.zeros(256, np.uint8))
            line[x:x + w] = img[j]
        tab[k] = (x, y, w, h, dx, dy)
    return canvas, tab

# ---------------------------------------------------------------------------------------------
# grada animada (A521h): 88x32 desde B338h en (40,16) y (128,16)
CHEER_X = (40, 128)
CHEER_Y = 16

def cheer_bits(f3):
    a = 0xB338 - 0x84D0
    return np.array([[bool(f3[a + y * 11 + x // 8] & (0x80 >> (x % 8))) for x in range(88)] for y in range(32)])

def cheer_images(f3, bits_bg, bg):
    """-> [img_izq, img_der]: colores del fondo donde el dibujo coincide; el resto se propaga
    desde los vecinos con el mismo bit (tinta = negro)"""
    from collections import Counter
    C = cheer_bits(f3)
    out = []
    for x0 in CHEER_X:
        Bn = bits_bg[CHEER_Y - 8:CHEER_Y - 8 + 32, x0:x0 + 88]
        img = bg[CHEER_Y:CHEER_Y + 32, x0:x0 + 88].copy()
        known = (C == Bn)
        img[C & ~known] = BLACK
        known |= C
        while not known.all():
            upd = []
            ys, xs = np.nonzero(~known)
            for y, x in zip(ys, xs):
                c = Counter()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        Y, X = y + dy, x + dx
                        if (dy or dx) and 0 <= Y < 32 and 0 <= X < 88 and known[Y, X] and not C[Y, X] and img[Y, X] != BLACK:
                            c[img[Y, X]] += 2 if dx == 0 or dy == 0 else 1
                if c: upd.append((y, x, c.most_common(1)[0][0]))
            if not upd:
                for y, x in zip(ys, xs): img[y, x] = SKIN; known[y, x] = True
                break
            for y, x, v in upd: img[y, x] = v; known[y, x] = True
        out.append(img)
    return out

# ---------------------------------------------------------------------------------------------
# marcador precalculado (estado del MSX1 al empezar el partido): imagen G4 de las filas 15-23 y
# sumas de control por celda (mismo calculo que RDCELL)
def sb_prerender():
    pat, col = pickle.load(open('/home/claude/w/s5_sbstate.pkl', 'rb'))
    lut = g2lut()
    img = np.zeros((72, 256), np.uint8); ck = bytearray(288)
    for r in range(9):
        for c in range(32):
            P = pat[r * 256 + c * 8:r * 256 + c * 8 + 8]; C = col[r * 256 + c * 8:r * 256 + c * 8 + 8]
            s = 0
            for b in list(P) + list(C):
                s = (s + b) & 255; s = ((s << 1) | (s >> 7)) & 255
            ck[r * 32 + c] = s | 1
            for l in range(8):
                fg, bg = lut[C[l] >> 4], lut[C[l] & 15]
                for k in range(8):
                    img[r * 8 + l, c * 8 + k] = fg if P[l] & (0x80 >> k) else bg
    return img, bytes(ck)
