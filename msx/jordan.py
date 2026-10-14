"""M. Jordan (NIVEL LEYENDA): piezas a partir de las de Romay (J_R, mismos rectangulos del atlas que
Romay) y de las de Itu (J_I, mismos rectangulos que Itu). Equipacion de EE.UU. en Los Angeles 84:
camiseta y pantalon azul marino con ribete rojo, calcetines y zapatillas blancos; piel oscura y pelo
corto. Las cabezas se dibujan a mano (las mismas para los dos juegos) dentro del recuadro de Itu."""
import numpy as np
from scipy import ndimage
import s5_assets as SA

SKIN_J = SA.BROWN          # piel
KIT = 13                   # azul marino (entrada 13 de la paleta, libre)
TRIM = SA.RED
B, W, T = SA.BLACK, SA.WHITE, 0

# cabezas (indice de Itu -> (x, y) de la esquina del dibujo dentro de la pieza, filas)
# '#' negro (contorno / pelo), 's' piel, 'w' blanco (ojos), '.' transparente
HEADS = {
    0x0B: (6, 3, [            # perfil (mira a la izquierda)
        '...######.',
        '..########',
        '.#########',
        '.##sss####',
        '#ss#s#s###',
        '#sssss#s##',
        '.#ssss#s#.',
        '#sssssss#.',
        '.#ss##ss#.',
        '..#ssss#..',
        '...#sss#..',
        '...#ss#...',
        '....##....']),
    0x17: (8, 3, [            # tres cuartos
        '..######..',
        '.########.',
        '##########',
        '#s##ss####',
        '#ws#sws###',
        '#sssss#s#.',
        '.#sssss##.',
        '#ssssss#..',
        '.#s##ss#..',
        '.#sssss#..',
        '..#sss#...',
        '..#ss#....',
        '...##.....']),
    0x23: (7, 3, [            # de frente
        '..######..',
        '.########.',
        '##########',
        '#s#ssss#s#',
        '#sw#ss#ws#',
        '#ssssssss#',
        '.#sss#ss#.',
        '.#ssssss#.',
        '.#s####s#.',
        '..#ssss#..',
        '...#ss#...',
        '...#ss#...',
        '....##....']),
    0x2F: (7, 3, [            # de espaldas
        '..######..',
        '.########.',
        '##########',
        '##########',
        '##########',
        '##########',
        '#s######s#',
        '.#ssssss#.',
        '..#ssss#..',
        '...#ss#...',
        '...#ss#...',
        '....##....']),
}
PAIRS = {0x0B: 0x0A, 0x17: 0x16, 0x23: 0x22, 0x2F: 0x2E, 0x33: 0x30, 0x34: 0x31, 0x35: 0x32,
         0x3A: 0x36, 0x3B: 0x37, 0x3C: 0x38, 0x3D: 0x39}
CH = {'#': B, 's': SKIN_J, 'w': W, '.': T, 'r': TRIM, 'k': KIT}


def head_img(i, shape):
    x0, y0, rows = HEADS[i]
    a = np.zeros(shape, np.uint8)
    for j, r in enumerate(rows):
        for k, c in enumerate(r):
            a[y0 + j, x0 + k] = CH[c]
    return a


def recolor(img, cls):
    """img: pieza de Itu o Romay (indices) ; cls: mapa de clases (S, R, L, W, O, #, .)"""
    a = img.copy()
    h = a.shape[0]
    a[img == SA.SKIN] = SKIN_J
    kitmask = np.isin(img, (SA.RED, SA.DBLUE))
    wm = img == SA.WHITE
    lab, n = ndimage.label(wm)
    ys = np.nonzero(img)[0]
    bottom = ys.max() if len(ys) else h
    for c in range(1, n + 1):
        m = lab == c
        top = np.nonzero(m)[0].min()
        if top < bottom - 9: kitmask |= m          # camiseta / pantalon (lo de abajo: calcetines y zapatillas)
    a[kitmask] = KIT
    # ribete rojo: borde de arriba de cada zona azul (cuello / cintura) junto al contorno
    return a


def shrink_hair(img, rows=14, it=3):
    """pelo corto: en las filas de la cabeza, el negro que no toca color desaparece (queda solo el
    contorno de 1 pixel) y se pone un casquete de 2 pixeles encima de la piel de la cara"""
    a = img.copy()
    col = (a != 0) & (a != B)
    near = ndimage.binary_dilation(col, structure=np.ones((3, 3)))
    rem = (a == B) & ~near
    rem[rows:] = False
    a[rem] = 0
    # casquete
    for x in range(a.shape[1]):
        ys = [y for y in range(min(rows, a.shape[0])) if a[y, x] == SKIN_J]
        if not ys: continue
        y = ys[0]
        for k in (1, 2):
            if y - k >= 0 and a[y - k, x] == 0: a[y - k, x] = B
    return a


def shrink_hair_old(img, rows=16, it=3):
    """pelo corto: quita capas exteriores del pelo negro en las primeras filas (sin tocar el contorno
    de la cara)"""
    a = img.copy()
    for _ in range(it):
        blk = a == B
        tr = a == 0
        col = (a != 0) & (a != B)
        near_col = ndimage.binary_dilation(col, structure=np.ones((3, 3)))
        tr_n = ndimage.binary_dilation(tr, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) | edge_mask(a)
        rem = blk & tr_n & ~near_col
        rem[rows:] = False
        a[rem] = 0
    return a


def back_head(a, cx=12.5, cy=8.5, rx=4.6, ry=5.6, rows=15):
    a = a.copy()
    col = (a != 0) & (a != B)
    near = ndimage.binary_dilation(col, structure=np.ones((3, 3)))
    for y in range(rows):
        for x in range(a.shape[1]):
            if a[y, x] != B: continue
            inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
            if not inside and not near[y, x]: a[y, x] = 0
    return a


def debeard(a, rows=16):
    """barba de Itu -> piel: negro entre pieles de la misma fila, por debajo de los ojos"""
    a = a.copy()
    sk = np.argwhere(a[:rows] == SKIN_J)
    if not len(sk): return a
    top = sk[:, 0].min()
    tr = ndimage.binary_dilation(a == 0, structure=np.ones((3, 3)))
    for y in range(top + 4, min(rows, top + 11)):
        xs = np.nonzero(a[y] == SKIN_J)[0]
        if len(xs) < 2: continue
        for x in range(xs.min() + 1, xs.max()):
            if a[y, x] == B and not tr[y, x]: a[y, x] = SKIN_J
    return a


def edge_mask(a):
    m = np.zeros(a.shape, bool); m[0, :] = m[-1, :] = True; m[:, 0] = m[:, -1] = True
    return m


def build(ps):
    """ps: SA.all_pieces(P) -> {'R': {i: img}, 'I': {i: img}} con la forma de la pieza original"""
    out = {'R': {}, 'I': {}}
    for slot, ch in (('R', 'romay'), ('I', 'itu')):
        for (c, i), img in ps.items():
            if c != ch: continue
            if i in HEADS or i in PAIRS.values() and slot == 'R' and i in (0x0A, 0x16, 0x22, 0x2E):
                continue
            j = recolor(img, None)
            if i in (0x3C, 0x3D):                      # Itu de espaldas: ya tiene el pelo corto
                pass
            elif i in (0x38, 0x39):                    # Romay de espaldas: cabeza ovalada
                j = back_head(j)
            elif i in (0x30, 0x31, 0x32, 0x36, 0x37):
                j = shrink_hair(j)
            elif i in (0x33, 0x34, 0x35, 0x3A, 0x3B):
                j = debeard(j)
            _, x0, y0 = SA.trim(img); t = SA.trim(img)[0]
            clip = np.zeros_like(j); clip[y0:y0 + t.shape[0], x0:x0 + t.shape[1]] = 1
            out[slot][i] = j * clip
    for hi, ri in list(PAIRS.items())[:4]:
        out['I'][hi] = head_img(hi, ps[('itu', hi)].shape)
        out['R'][ri] = head_img(hi, ps[('romay', ri)].shape)
    return out


# ---------------------------------------------------------------------------------------------
# Jordan con la altura de Itu en el sitio de Romay (cuando el humano juega con Itu): las piezas de
# J_I se reparten por los rectangulos de Romay y las filas libres del atlas; la tabla del atlas
# del juego de Romay se cambia por la de Jordan.
INV = {v: k for k, v in PAIRS.items()}          # indice de Romay -> el de Itu


def free_rects(tab):
    """rectangulos de Romay + filas libres de cada zona del atlas -> [(x, y, w, h)]"""
    rects = []
    for (c, i), (x, y, w, h, dx, dy) in tab.items():
        if c == 'romay': rects.append([x, y, w + (w & 1), h])
    for ry, rh in SA.REGIONS:
        used = [y + h for (x, y, w, h, dx, dy) in tab.values() if ry <= y < ry + rh]
        top = max(used) if used else ry
        if top < ry + rh: rects.append([0, top, 256, ry + rh - top])
    return rects


def pack_into(rects, items):
    """guillotina: items {clave: img recortada} -> {clave: (x, y)}"""
    free = [list(r) for r in rects]
    pos = {}
    for k in sorted(items, key=lambda k: (-items[k].shape[0], -items[k].shape[1])):
        h, w = items[k].shape; w2 = w + (w & 1)
        best = None
        for n, (x, y, fw, fh) in enumerate(free):
            if w2 <= fw and h <= fh:
                waste = fw * fh - w2 * h
                if best is None or waste < best[0]: best = (waste, n)
        if best is None: raise ValueError('Jordan no cabe en el atlas: %r %dx%d' % (k, w, h))
        x, y, fw, fh = free.pop(best[1])
        pos[k] = (x, y)
        # resto a la derecha (alto h) y debajo (ancho completo)
        if fw - w2 > 0: free.append([x + w2, y, fw - w2, h])
        if fh - h > 0: free.append([x, y + h, fw, fh - h])
    return pos


def romay_slot(J, tab):
    """-> (piezas [(x, y, img)], entradas ATAB de 62 x 7 para el juego de Romay)"""
    JI = J['I']
    src = {}
    for i in range(62):
        k = INV.get(i, i)
        if k in JI: src[i] = k
    items = {}
    trims = {}
    for i, k in src.items():
        t, dx, dy = SA.trim(JI[k])
        trims[i] = (t, dx, dy)
    uniq = {}
    for i, k in src.items(): uniq.setdefault(k, i)
    for k, i in uniq.items(): items[k] = trims[i][0]
    pos = pack_into(free_rects(tab), items)
    ent = bytearray()
    for i in range(62):
        if i not in src:
            ent += bytes(7); continue
        k = src[i]; t, dx, dy = trims[i]; x, y = pos[k]
        ent += bytes([x, y & 255, y >> 8, t.shape[1], t.shape[0], dx, dy])
    pieces = [(pos[k], items[k]) for k in items]
    return pieces, bytes(ent)
