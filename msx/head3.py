"""Cabeza caricaturesca para la presentacion MSX (40x48, blanco/negro).
Proporciones tomadas de la caricatura en espejo: pelo enorme, oreja grande a la derecha,
coleta tras la oreja, cejas gruesas, ojos pequenos entornados, nariz muy larga y bulbosa,
sonrisa ancha con dientes, menton estrecho."""
import numpy as np
from PIL import Image, ImageDraw

W, H = 40, 48

def m(fn):
    im = Image.new('L', (W, H), 0); fn(ImageDraw.Draw(im)); return np.array(im) > 0

def E(d, cx, cy, rx, ry, f=255): d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=f)

FACE = [(7, 22), (26, 18), (28, 24), (27, 31), (25, 36), (22, 41), (19, 45), (17, 45), (15, 42), (13, 38), (10, 33), (8, 28)]

def dil(M):
    D = M.copy()
    D[1:, :] |= M[:-1, :]; D[:-1, :] |= M[1:, :]; D[:, 1:] |= M[:, :-1]; D[:, :-1] |= M[:, 1:]
    return D

def build():
    yy, xx = np.mgrid[0:H, 0:W]
    def hair_fn(d):
        E(d, 19, 12, 17, 11)
        E(d, 6, 24, 4.5, 8)
        E(d, 29, 15, 8, 6)
        for cx, cy, r in ((6, 6, 3.5), (12, 3, 3.5), (19, 2.5, 3.5), (26, 3, 3.5), (32, 6, 3.5), (35, 11, 3), (3, 12, 3), (3, 18, 2.5), (35, 16, 2.5)):
            E(d, cx, cy, r, r)
    hair = m(hair_fn)
    pony = m(lambda d: E(d, 31, 34, 2.5, 4.5))
    ear = m(lambda d: E(d, 30, 24, 3.5, 6.5))
    face = m(lambda d: d.polygon(FACE, fill=255))
    neck = m(lambda d: d.polygon([(16, 42), (24, 38), (26, 47), (15, 47)], fill=255))
    hl = 18 + (26 - xx) * (6 / 19)
    skin = ((face & (yy >= hl)) | ear | neck)
    hair_all = (hair | pony) & ~skin
    bgm = ~(hair_all | skin)
    img = skin.copy()
    img |= hair_all & dil(bgm)              # contorno blanco del pelo contra el fondo
    # separar coleta del pelo y de la oreja
    img |= pony & dil(hair & ~pony) & ~skin
    im = Image.fromarray((img * 255).astype('uint8')); d = ImageDraw.Draw(im)
    for x, y in ((8, 7), (14, 5), (21, 5), (27, 7), (11, 11), (18, 10), (25, 11), (31, 12), (6, 15), (14, 15), (21, 15), (4, 21), (5, 27), (30, 34)):
        for dx, dy in ((0, 1), (1, 0), (2, 0), (3, 1)):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and hair_all[Y, X]: d.point((X, Y), 255)
    # oreja: borde frontal y pabellon
    d.line([(27, 19), (26, 24), (27, 29)], fill=0)
    d.arc([28, 19, 32, 29], 300, 60, fill=0)
    # cejas gruesas
    d.polygon([(14, 23), (16, 21), (20, 20), (24, 20), (23, 22), (19, 22), (16, 24)], fill=0)
    d.polygon([(6, 26), (8, 24), (12, 24), (13, 25), (9, 26), (7, 27)], fill=0)
    # ojos entornados
    d.polygon([(16, 25), (20, 24), (22, 25), (18, 26)], fill=0); d.point((19, 25), 255)
    d.polygon([(8, 28), (11, 27), (13, 28), (10, 29)], fill=0); d.point((11, 28), 255)
    # nariz larga y bulbosa
    d.line([(15, 26), (14, 30), (13, 35), (13, 37)], fill=0)
    d.line([(17, 28), (17, 32), (18, 35)], fill=0)
    d.arc([11, 35, 19, 43], 20, 210, fill=0)
    d.point((16, 39), 0); d.point((17, 39), 0)
    # mejilla
    d.line([(11, 31), (12, 34)], fill=0)
    # sonrisa ancha con dientes
    d.polygon([(19, 35), (23, 34), (26, 31), (26, 33), (24, 37), (21, 39), (19, 38)], fill=0)
    d.line([(20, 36), (23, 35), (25, 33)], fill=255)
    d.line([(21, 37), (23, 36)], fill=255)
    # menton
    d.line([(17, 44), (19, 44)], fill=0)
    return np.array(im) > 0

if __name__ == '__main__':
    h = build()
    Image.fromarray((h * 255).astype('uint8')).resize((W * 10, H * 10), Image.NEAREST).save('head3.png')
