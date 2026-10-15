"""Karnov en el publico del MSX1 (a partir de la plantilla del publico del MSX2 retocada por el usuario).
Solo los pixeles que cambio el usuario respecto a la plantilla anterior: tinta = negro o marron del MSX2.
Fondo del publico: bitmap de B498h (filas 0-47 = y 8-55, x 32-223 = columnas 0-191 de la plantilla).
Publico animado: bitmap de B338h (88x32, el mismo para los dos rectangulos de x 40 y 128, y 16-47)."""
import numpy as np
from court import court_bits, put_bits

OLD = 'bf4be852-image.png'
INK = (1, 12)
CB = 0xB338


def masks():
    import user_art, s5_import as SI
    new_pub = np.array(user_art.D['pub']).astype(int)
    new_ch = [np.array(c).astype(int) for c in user_art.D['cheers']]
    keep = SI.FILES['publico']
    SI.FILES['publico'] = OLD
    try:
        old_pub, old_ch = SI.publico()
    finally:
        SI.FILES['publico'] = keep
    tonum = lambda a: np.vectorize(lambda v: 13 if v == '13o' else int(v))(np.array(a, dtype=object))
    old_pub = tonum(old_pub); old_ch = [tonum(c) for c in old_ch]
    return (new_pub, new_pub != old_pub), (new_ch[0], new_ch[0] != old_ch[0])


def apply(F1, F2, F3):
    (pub, dp), (ch, dc) = masks()
    b = court_bits(F3)
    ys, xs = np.nonzero(dp)
    for y, x in zip(ys, xs):
        b[y, 32 + x] = pub[y, x] in INK
    put_bits(F3, b)
    a = CB - 0x84D0
    ys, xs = np.nonzero(dc)
    for y, x in zip(ys, xs):
        i = a + y * 11 + x // 8; m = 0x80 >> (x % 8)
        F3[i] = (F3[i] | m) if ch[y, x] in INK else (F3[i] & ~m & 255)
