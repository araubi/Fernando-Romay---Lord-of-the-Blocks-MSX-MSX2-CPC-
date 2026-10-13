"""Cabeza caricaturesca de perfil (mirando a la izquierda) para la ventana animada 32x56
(x 48-79, y 8-63). Filas 46-55 de la ventana: cuello/tirantes del original."""
import numpy as np
from PIL import Image, ImageDraw
from frames import frame

W, H = 32, 56

def m(fn):
    im = Image.new('L', (W, H), 0); fn(ImageDraw.Draw(im)); return np.array(im) > 0

def E(d, cx, cy, rx, ry, f=255): d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=f)

def dil(M):
    D = M.copy()
    D[1:, :] |= M[:-1, :]; D[:-1, :] |= M[1:, :]; D[:, 1:] |= M[:, :-1]; D[:, :-1] |= M[:, 1:]
    return D

def orig_rows():
    _, dat = frame(0xC41E, 0, 4, 56)
    return np.array([[bool(dat[y * 4 + x // 8] & (0x80 >> (x % 8))) for x in range(32)] for y in range(56)])

# perfil: frente, cejon, nariz enorme, labios, menton saliente, mandibula hasta el cuello
FACE = [(9, 15), (7, 17), (5, 19), (6, 21), (5, 23), (3, 25), (1, 28), (0, 31), (0, 34), (1, 36),
        (5, 36), (6, 37), (5, 38), (4, 40), (5, 41), (3, 43), (3, 45), (5, 47), (9, 46), (12, 44),
        (11, 47), (21, 47), (21, 40), (22, 33), (23, 25), (21, 15)]

def base():
    yy, xx = np.mgrid[0:H, 0:W]
    def hair_fn(d):
        E(d, 16.5, 13, 14, 11.5)
        for cx, cy, r in ((5, 6, 3.5), (11, 4, 3.5), (18, 3.5, 3.5), (25, 5.5, 3.5), (29, 10, 2.5), (3, 12, 3)):
            E(d, cx, cy, r, r)
        E(d, 26.5, 26, 4, 13)            # pelo de la nuca, cae tras la oreja
        E(d, 25, 18, 6, 6)
    hair = m(hair_fn)
    face = m(lambda d: d.polygon(FACE, fill=255))
    ear = m(lambda d: E(d, 17, 28, 3, 5))
    neck = m(lambda d: d.polygon([(9, 47), (12, 41), (21, 38), (21, 47)], fill=255))
    hl = np.where(xx < 12, 16 + 0 * xx, 16 + (xx - 12) * 0.2)
    sideburn = (xx >= 11) & (xx <= 13) & (yy <= 25)
    skin = (((face | neck) & (yy >= hl)) | ear) & ~sideburn
    hair_all = hair & ~skin
    hair_all[46:, :] = False
    img = skin.copy()
    img |= hair_all & dil(~(hair_all | skin))     # contorno blanco del pelo
    img[46:, :] = False
    return img, hair_all, skin

CURLS = ((6, 6), (12, 4), (19, 4), (24, 7), (9, 10), (16, 9), (22, 11), (5, 13), (13, 13), (20, 15), (26, 20), (26, 27), (27, 33))

def build(expr=0):
    img, hair_all, skin = base()
    im = Image.fromarray((img * 255).astype('uint8')); d = ImageDraw.Draw(im)
    P = lambda pts, c=0: [d.point(p, c) for p in pts]
    for x, y in CURLS:
        for dx, dy in ((0, 1), (1, 0), (2, 0), (3, 1)):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < 46 and hair_all[Y, X]: d.point((X, Y), 255)
    # oreja (contorno y pabellon)
    # cejon grueso que sobresale
    if expr == 7:
        P([(4, 18), (5, 17), (6, 17), (7, 17), (8, 17), (9, 18), (5, 18), (6, 18), (7, 18), (8, 18)])
    else:
        P([(4, 19), (5, 18), (6, 18), (7, 18), (8, 18), (9, 19), (5, 19), (6, 19), (7, 19), (8, 19)])
    # ojo pequeno y entornado (cerrado en la carcajada)
    if expr in (2, 4):
        P([(6, 22), (7, 21), (8, 21), (9, 22)])
    else:
        P([(6, 21), (7, 21), (8, 21), (9, 21), (7, 22), (8, 22)])
        P([(7, 21)], 255)
    P([(10, 23), (11, 24)])
    # nariz enorme: aleta y fosa
    P([(7, 27), (8, 29), (8, 31), (7, 33), (6, 34)])
    P([(3, 35), (4, 35)])
    # pomulo y surco nasogeniano
    P([(12, 29), (13, 31), (13, 33)])
    P([(9, 34), (10, 36), (10, 38)])
    # mandibula
    P([(13, 44), (14, 43), (15, 42), (16, 41), (17, 40), (18, 39), (19, 38), (20, 37)])
    # boca
    if expr in (0, 1, 2):
        P([(5, 39), (6, 39), (7, 38), (8, 38), (9, 37)])
        if expr == 1: P([(10, 36), (9, 36)])
    elif expr in (3, 4):
        for y in range(38, 42 + (expr == 4)):
            for x in range(4, 10 - (y - 38) // 2):
                d.point((x, y), 0)
        P([(5, 38), (6, 38), (7, 38)], 255)
        P([(9, 37), (10, 36)])
    else:
        w = {5: 8, 6: 9, 7: 10}[expr]
        P([(x, 38) for x in range(4, w + 1)] + [(w + 1, 37)])
        P([(x, 39) for x in range(5, w)], 255); P([(4, 39), (w, 39)])
        P([(x, 40) for x in range(5, w)])
        P([(6, 39), (8, 39)] + ([(10, 38)] if w >= 10 else []))
    # hoyuelo del menton y mandibula
    P([(4, 44)])
    out = np.array(im) > 0
    out = big_ear(out)
    out = user_fix(out)
    o = orig_rows()
    out[46:, :] = o[46:, :]                                      # cuello y tirantes originales
    return out

def big_ear(out):
    """oreja grande ovalada (x 14-21, filas 18-34) con pelo encima, segun la correccion del usuario"""
    im = Image.fromarray((out * 255).astype('uint8')); d = ImageDraw.Draw(im)
    d.rectangle([13, 14, 21, 17], fill=0)                  # pelo junto a la oreja
    d.ellipse([14, 18, 21, 34], fill=255)                   # oreja
    d.ellipse([14, 18, 21, 34], outline=0)                  # contorno
    d.arc([16, 20, 20, 30], 250, 80, fill=0)                # helix (borde interior)
    d.line([(17, 24), (17, 27)], fill=0)                    # concha
    return np.array(im) > 0

# retoques del usuario sobre la pantalla de carga (coordenadas de pantalla)
USER_BLACK = [(62, 26), (62, 27), (69, 25), (70, 25), (69, 26), (70, 26), (69, 27), (70, 27), (69, 28), (70, 28),
              (65, 28), (64, 29), (65, 36), (66, 37)]
USER_WHITE = [(64, 36), (64, 37), (63, 38), (62, 31), (62, 32), (62, 33), (61, 34), (62, 34), (61, 35), (62, 35), (62, 36), (62, 37)]
def user_fix(out):
    for x, y in USER_BLACK: out[y - 8, x - 48] = False
    for x, y in USER_WHITE: out[y - 8, x - 48] = True
    return out

FRAMES = [0, 1, 2, 3, 4, 5, 6, 7]

if __name__ == '__main__':
    ims = []
    for e in FRAMES:
        h = build(e)
        ims.append(Image.fromarray((h * 255).astype('uint8')).resize((W * 8, H * 8), Image.NEAREST))
    sheet = Image.new('L', ((W * 8 + 8) * 4, (H * 8 + 8) * 2), 90)
    for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * (W * 8 + 8), (i // 4) * (H * 8 + 8)))
    sheet.save('head5_frames.png')
