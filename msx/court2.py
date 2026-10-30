"""Cancha MSX2 al estilo de la final olimpica de 1984 (parquet claro, zonas y circulo verde
azulado, lineas, estrella y aros en blanco).
Modo G3: 2 colores por tramo de 8x1. El fondo del juego (B498h, 1 bit) se redibuja para las
filas de caracteres 8..14 de pantalla y se genera un mapa de color por byte.
Bits a 1 = color de tinta del tramo; la tinta de los jugadores sera siempre negra (ver msx2_sprite)."""
import numpy as np, pickle
from scipy import ndimage
import court_patch as CP

# paleta (indice -> RGB 0..7)
PARQ, TEAL, WHITE, BLACK = 4, 11, 15, 1
OUTSIDE = PARQ
GREY = 13
PAL = {PARQ: (7, 6, 4), TEAL: (3, 6, 5), GREY: (4, 4, 4)}
Y0 = 56            # fila del buffer (pantalla y=64, fila de caracteres 8)

def classify(bits):
    """bits: 112x256 del fondo actual -> imagen objetivo (56x256) de indices de color"""
    B = bits[Y0:]
    H = B.shape[0]
    p = np.pad(B, 1)
    n4 = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    d4 = p[:-2, :-2].astype(int) + p[:-2, 2:] + p[2:, :-2] + p[2:, 2:]
    dith = B & (n4 == 0) & (d4 >= 2)
    nonline = ~B | dith
    lab, n = ndimage.label(nonline)
    T = np.full(B.shape, PARQ, np.uint8)
    # exterior: bits a 1 macizos unidos a los bordes izquierdo/derecho
    solid, _ = ndimage.label(B & ~dith)
    out = np.zeros_like(B)
    for k in set(solid[:, 0]) | set(solid[:, -1]):
        if k: out |= solid == k
    sizes = ndimage.sum(np.ones_like(lab), lab, range(n + 1))
    # zonas verdes: componentes con trama (zonas) y circulo central
    star, circ = CP.logo_layers(CP.PARAMS['R'], CP.PARAMS['r'])
    circ = circ[Y0:]; star = star[Y0:]
    teal = np.zeros_like(B)
    for k in range(1, n + 1):
        m = lab == k
        if (dith & m).sum() > 20 and not (m & star).any(): teal |= m
        if (m & circ).sum() > 0.6 * m.sum() and m.sum() > 30: teal |= m
    # franja del fondo (entre el cartel y la linea de fondo) y laterales: verde
    strip = lab == lab[2, 128]
    T[teal | strip] = TEAL
    T[out] = OUTSIDE
    lines = B & ~dith & ~out
    T[lines] = WHITE
    # trama fuera de las zonas (sombra de la estrella): verde
    yy, xx = np.mgrid[0:H, 0:256]
    shadow_zone = (xx > CP.CX) & (xx < 175) & (yy < 40)
    T[dith & ~teal & shadow_zone] = TEAL
    # puntos sueltos del borde de las zonas -> verde
    near = ndimage.binary_dilation(teal & ~strip, iterations=2)
    T[B & near & (n4 <= 1) & ~circ] = TEAL
    return T

def to_g3(T):
    """objetivo -> (bits, colores) con 2 colores por tramo; tinta negra si el tramo es de un color"""
    H = T.shape[0]
    bits = np.zeros(T.shape, bool); col = np.zeros((H, 32), np.uint8); err = 0
    for y in range(H):
        for cx in range(32):
            seg = T[y, cx * 8:cx * 8 + 8]
            vals, cnt = np.unique(seg, return_counts=True)
            order = sorted(zip(cnt, vals), reverse=True)
            if len(order) == 1:
                col[y, cx] = (BLACK << 4) | order[0][1]; continue
            # fondo = el mas frecuente (en empate, el no blanco); tinta = el siguiente
            (c1, v1), (c2, v2) = order[0], order[1]
            if c1 == c2 and v1 == WHITE: v1, v2 = v2, v1
            bg, fg = v1, v2
            if len(order) > 2:
                # tres colores: la linea blanca se funde con el verde (borde de zona)
                if set(vals) == {WHITE, TEAL, PARQ}:
                    seg = np.where(seg == WHITE, TEAL, seg)
                    vals, cnt = np.unique(seg, return_counts=True)
                    order = sorted(zip(cnt, vals), reverse=True)
                    (c1, v1), (c2, v2) = order[0], order[1]
                    bg, fg = v1, v2
                    if bg == WHITE: bg, fg = fg, bg
                err += sum(c for c, v in order if v not in (bg, fg))
            bits[y, cx * 8:cx * 8 + 8] = seg == fg
            col[y, cx] = (fg << 4) | bg
    return bits, col, err

def render(bits, col, pal_rgb):
    H = bits.shape[0]
    img = np.zeros((H, 256, 3), np.uint8)
    for y in range(H):
        for x in range(256):
            c = col[y, x // 8]; i = (c >> 4) if bits[y, x] else (c & 15)
            img[y, x] = pal_rgb[i]
    return img

def build(bits):
    T = classify(bits)
    nb, col, err = to_g3(T)
    full = bits.copy(); full[Y0:] = nb
    return T, full, col, err

if __name__ == '__main__':
    from PIL import Image
    v, r, reg, pal = pickle.load(open('../out/st600.pkl', 'rb'))
    b = np.unpackbits(np.frombuffer(r[0xB498:0xB498 + 0xE00], np.uint8)).reshape(112, 256).astype(bool)
    T, full, col, err = build(b)
    print('pixeles con color perdido:', err)
    P = [tuple(x * 255 // 7 for x in pal[i]) for i in range(16)]
    for k, (rr, g, bb) in PAL.items(): P[k] = (rr * 255 // 7, g * 255 // 7, bb * 255 // 7)
    tgt = np.array([P[i] for i in T.flat], np.uint8).reshape(T.shape + (3,))
    g3 = render(full[Y0:], col, P)
    Image.fromarray(np.vstack([tgt, g3])).resize((1024, 448), Image.NEAREST).save('../out/court2.png')


# ---------------------------------------------------------------------------------------------
# datos para la ROM: mapa de colores (VRAM 2800h-2EFFh) y paquete en RAM (indice de celdas
# mixtas + colores estaticos + rutina COURTC llamada desde PASS)
CPACK = 0xED00            # indice de celdas (7 filas x 32) alineado
CC_M = CPACK + 0xE0
CODE = CPACK + 0xE8        # codigo del paquete (COMPOSE, COURTC: msx2_sprite.SRCP)
MIX = CODE + 0x308         # colores de las celdas mixtas (sin repetir), a partir del bloque NSEG2+1
SEG2 = 0xE760              # segundo trozo del paquete: primeros NSEG2 bloques de colores
NSEG2 = 20
PACK_LIMIT = 0xF280
ROW0 = 7                  # fila de caracteres del buffer (pantalla 8)

COURTC_SRC = f"""
; C = fila de caracteres del buffer (7..13), E = columna. Acarreo = celda tratada aqui.
COURTC:
  ld a,c
  sub {ROW0}
  rrca
  rrca
  rrca
  add a,e
  ld l,a
  ld h,{CPACK >> 8}
  ld a,(hl)
  or a
  ret z
  ld ({CC_M + 1}),hl
  and 7Fh
  push de
  push bc
  ld l,a
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  cp {NSEG2 + 1}
  jr c,cc_s2
  ld a,l
  add a,{(MIX - 8 - NSEG2 * 8) & 255}
  ld l,a
  ld a,h
  adc a,{(MIX - 8 - NSEG2 * 8) >> 8}
  jr cc_s3
cc_s2:
  ld a,l
  add a,{(SEG2 - 8) & 255}
  ld l,a
  ld a,h
  adc a,{(SEG2 - 8) >> 8}
cc_s3:
  ld h,a
  push hl
  ld a,c
  add a,0C2h
  ld h,a
  ld a,e
  add a,98h
  ld l,a
  ld c,l
  ld a,h
  sub 0Eh
  ld b,a
  ld e,8
cc_1:
  ld a,(bc)
  cp (hl)
  jr z,cc_e
  cpl
  and (hl)
  out (98h),a
  scf
  jr cc_n
cc_e:
  out (98h),a
  or a
cc_n:
  rl d
  ld a,l
  add a,32
  ld l,a
  ld c,a
  jr nc,cc_x
  inc h
  inc b
cc_x:
  dec e
  jr nz,cc_1
  ld a,d
  ld ({CC_M}),a
  ; colores: solo si hay tinta ahora o la hubo la ultima vez (bit 7 del indice)
  ld hl,({CC_M + 1})
  or a
  jr nz,cc_dy
  bit 7,(hl)
  jr z,cc_sk
  res 7,(hl)
  jr cc_wc
cc_dy:
  set 7,(hl)
cc_wc:
  pop hl
  pop bc
  pop de
  push de
  push bc
  ld a,e
  add a,a
  add a,a
  add a,a
  di
  out (99h),a
  ld a,c
  inc a
  or 60h
  out (99h),a
  ei
  ld a,({CC_M})
  ld c,a
  ld b,8
cc_2:
  ld a,(hl)
  inc hl
  sla c
  jr nc,cc_o
  and 0Fh
  or 10h
cc_o:
  out (98h),a
  djnz cc_2
  pop bc
  pop de
  scf
  ret
cc_sk:
  pop hl
  pop bc
  pop de
  scf
  ret
"""


# ---- v3: retoques del usuario (captura editada, court_user_v3.png) ----
UCOL = {(0, 0, 0): BLACK, (255, 218, 145): PARQ, (109, 218, 182): TEAL, (255, 255, 255): WHITE,
        (72, 109, 255): 5, (218, 218, 36): 10, (255, 182, 109): 12, (129, 129, 129): GREY,
        (72, 218, 255): 7, (255, 36, 36): 2, (36, 72, 218): 6}
def user_indices():
    from PIL import Image
    u = np.asarray(Image.open('court_user_v3.png').convert('RGB')).astype(int)
    keys = list(UCOL); arr = np.array(keys)
    d = ((u[:, :, None, :] - arr[None, None]) ** 2).sum(3)
    return np.array([UCOL[k] for k in keys], np.uint8)[d.argmin(2)]

def top_colours(bits):
    """filas de pantalla 8..63: bits del juego intactos (la grada animada y los aros los escribe el
    juego); color de tinta = el que el usuario puso en los pixeles a 1, fondo = el de los pixeles a 0"""
    from collections import Counter
    U = user_indices()
    v, r, reg, pal = pickle.load(open('court_ref540.pkl', 'rb'))
    mask = pickle.load(open('court_pmask.pkl', 'rb'))
    col = np.zeros((56, 32), np.uint8)
    for y in range(8, 64):
        for cx in range(32):
            hoop = cx < 5 or cx >= 27
            pv = v[(y // 8) * 256 + cx * 8 + (y & 7)]
            ref = pv if hoop else int(''.join('1' if q else '0' for q in bits[y - 8, cx * 8:cx * 8 + 8]), 2)
            if mask[y, cx * 8] and not hoop:
                col[y - 8, cx] = v[0x2000 + (y // 8) * 256 + cx * 8 + (y & 7)]; continue
            if hoop:      # tablero completamente verde (sin el parquet interior)
                for k in range(8):
                    if U[y, cx * 8 + k] == PARQ: U[y, cx * 8 + k] = TEAL
            on = [U[y, cx * 8 + k] for k in range(8) if ref & (0x80 >> k)]
            off = [U[y, cx * 8 + k] for k in range(8) if not ref & (0x80 >> k)]
            fg = Counter(on).most_common(1)[0][0] if on else BLACK
            bg = Counter(off).most_common(1)[0][0] if off else fg
            if not on: fg = BLACK
            col[y - 8, cx] = (fg << 4) | bg
    return col

def build3(bits):
    U = user_indices()
    mask = pickle.load(open('court_pmask.pkl', 'rb'))
    T_old = classify(bits)
    T = np.where(mask[64:120], T_old, U[64:120]).astype(np.uint8)
    nb, col, err = to_g3(T)
    full = bits.copy(); full[Y0:] = nb
    return T, full, col, top_colours(bits), err

def tables(bits, packcode=None):
    """bits: fondo actual 112x256 -> (bits nuevos, mapa VRAM filas 1..14, paquete RAM, etiquetas)"""
    from asm import assemble
    T, full, col, top, err = build3(bits)
    vmap = bytearray()
    for r in range(7):
        for cx in range(32):
            for j in range(8): vmap.append(int(top[r * 8 + j, cx]))
    for r in range(7):
        for cx in range(32):
            for j in range(8): vmap.append(int(col[r * 8 + j, cx]))
    cidx = bytearray(224); blocks = []
    for r in range(7):
        for cx in range(32):
            cs = bytes(int(col[r * 8 + j, cx]) for j in range(8))
            if all(c >> 4 == BLACK for c in cs): continue
            if cs not in blocks: blocks.append(cs)
            cidx[r * 32 + cx] = blocks.index(cs) + 1
    n = len(blocks); seg2 = b''.join(blocks[:NSEG2]); mix = b''.join(blocks[NSEG2:])
    assert n < 256
    if packcode is None:
        import msx2_sprite
        packcode = msx2_sprite.packcode()
    assert len(packcode) <= MIX - CODE, len(packcode)
    pack = bytes(cidx) + bytes(CODE - CPACK - 224) + packcode.ljust(MIX - CODE, b'\0') + mix
    assert CPACK + len(pack) <= PACK_LIMIT, hex(CPACK + len(pack))
    L = {'COURTC': CODE}
    return full, bytes(vmap), pack, {'COURTC': L['COURTC'], 'PACKLEN': len(pack), 'NMIX': n, 'SEG2': seg2}


def zoom_table(vmap):
    """tabla de colores (6144) de la repeticion: ampliacion x2 de las filas 8..103 del buffer, bytes 0..15"""
    out = bytearray(6144)
    for y in range(192):
        r = 8 + y // 2
        for C in range(32):
            col = C // 2
            out[(y // 8) * 256 + C * 8 + (y % 8)] = vmap[(r // 8) * 256 + col * 8 + (r % 8)]
    return bytes(out)


def court_bits_f3(F3):
    from court import court_bits
    return court_bits(F3)


def apply(F1, F2, F3):
    from court import court_bits, put_bits
    full, vmap, pack, L = tables(court_bits(F3))
    put_bits(F3, full)
