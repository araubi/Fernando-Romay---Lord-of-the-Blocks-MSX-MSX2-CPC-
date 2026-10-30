"""Lectura de las plantillas retocadas por el usuario (bloques de 4x4 -> color de la paleta)."""
import numpy as np
from PIL import Image
import s5_assets as SA
import s5_sheets as SH

S = SH.S
OLD13 = (6, 5, 3)          # el 13 antiguo (las plantillas se hicieron con el)

def palette_rgb(old13=True):
    pal = {i: SA.rgb8(c) for i, c in SA.PAL.items() if i != 0}
    if old13: pal['13o'] = SA.rgb8(OLD13)
    return pal

def sample(im, x, y, w, h, transp=False, pal=None):
    """bloque de w x h pixeles del MSX en (x, y) de la plantilla -> matriz de indices (o '13o')"""
    pal = pal or palette_rgb()
    a = np.asarray(im.convert('RGB')).astype(int)
    out = np.zeros((h, w), object)
    keys = list(pal); P = np.array([pal[k] for k in keys])
    for j in range(h):
        for i in range(w):
            blk = a[y + j * S:y + j * S + S, x + i * S:x + i * S + S].reshape(-1, 3)
            c = a[y + j * S + S // 2, x + i * S + S // 2]
            if transp and abs(c[0] - 255) < 40 and c[1] < 60 and abs(c[2] - 255) < 40:
                out[j, i] = 0; continue
            # color mayoritario del bloque (lo dibujado fuera de la rejilla de 4x4 cuenta por cobertura;
            # el blanco y el negro pesan la mitad para que no se coman los trazos finos)
            d = ((blk[:, None, :] - P[None, :, :]) ** 2).sum(-1).argmin(1)
            cnt = {}
            for n in d:
                k = keys[n]; cnt[k] = cnt.get(k, 0) + (0.5 if k in (1, 15) else 1)
            out[j, i] = max(cnt, key=cnt.get)
    return out

U = '../art/'
FILES = {'jordan': 'a3f99c49-image.png', 'publico': 'd8d8b495-image.png', 'canastas': 'd119befc-image.png',
         'presentacion': 'd2d8dbb6-image.png', 'cancha': 'fef1eda4-image.png', 'marcador': '43494d43-image.png'}
M, T = SH.MARGIN, SH.TITLE_H


def img(name):
    return Image.open(U + FILES[name])


def cancha():
    return sample(img('cancha'), M, M + T, 256, 64)


def publico():
    im = img('publico')
    pub = sample(im, M, M + T, 192, 48)
    y2 = M + T + 48 * S + M + T
    lev = sample(im, M, y2, 192, 48)
    cheers = [lev[8:40, x0 - 32:x0 - 32 + 88] for x0 in (40, 128)]
    return pub, cheers


def canastas():
    im = img('canastas')
    y = M + T
    left = sample(im, M, y, 32, 48); y += 48 * S + M + T
    right = sample(im, M, y, 32, 48); y += 48 * S + M
    nets = {}
    for base in (0x3E, 0x43):
        y += T
        for k in range(5):
            X = M + k * (24 * S + 12)
            nets[base + k] = sample(im, X, y, 24, 24, transp=True)
        y += 24 * S + M
    return left, right, nets


def marcador():
    return sample(img('marcador'), M, M + T, 256, 72)


def presentacion():
    import pres_color as PC
    im = img('presentacion')
    y = M + T
    pic = sample(im, M, y, 256, 192); y += 192 * S + M
    frames = {}
    for keys, (w, h) in ((PC.HEADS, (32, 56)), (PC.BALLS, (32, 32)), (PC.HANDS_ALL, (24, 24))):
        y += T
        x = M
        for k in keys:
            frames[k] = sample(im, x, y, w, h); x += w * S + 12
        y += h * S + M
    return pic, frames


def jordan(shapes):
    """shapes: {indice: forma (h, w)} en el orden de la plantilla"""
    im = img('jordan')
    ks = sorted(shapes)
    y = M + T
    out = {}
    for n, k in enumerate(ks):
        x = M + (n % 10) * (26 * S + 8); yy = y + (n // 10) * (44 * S + T)
        h, w = shapes[k]
        out[k] = sample(im, x, yy + 12, w, h, transp=True)
    return out
