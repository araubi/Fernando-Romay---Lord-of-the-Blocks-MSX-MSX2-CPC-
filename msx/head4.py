"""Cabeza caricaturesca 40x48 (blanco/negro) para la presentacion MSX.
Rasgos tomados de la caricatura (en espejo, para que mire hacia el balon)."""
import numpy as np
from PIL import Image, ImageDraw

W, H = 40, 48

def m(fn):
    im = Image.new('L', (W, H), 0); fn(ImageDraw.Draw(im)); return np.array(im) > 0

def E(d, cx, cy, rx, ry, f=255): d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=f)

def dil(M):
    D = M.copy()
    D[1:, :] |= M[:-1, :]; D[:-1, :] |= M[1:, :]; D[:, 1:] |= M[:, :-1]; D[:, :-1] |= M[:, 1:]
    return D

# contorno de la cara (incluye nariz que sobresale abajo-izquierda y menton)
FACE = [(9, 21), (26, 17), (27, 30), (27, 35), (26, 38), (24, 41), (22, 43), (20, 45), (17, 46), (15, 44),
        (13, 43), (11, 41), (10, 38), (10, 35), (9, 32), (8, 27)]
NECK = [(18, 46), (24, 41), (27, 38), (28, 47), (17, 47)]

def build():
    yy, xx = np.mgrid[0:H, 0:W]
    def hair_fn(d):
        E(d, 19, 12, 17, 11)
        E(d, 5.5, 23, 4, 8.5)                      # mechon que cae por la izquierda
        E(d, 29, 14, 8, 6)
        for cx, cy, r in ((6, 6, 3.5), (12, 3, 3.5), (19, 2.5, 3.5), (26, 3, 3.5), (32, 6, 3.5),
                          (35, 11, 3), (3, 12, 3), (3, 18, 2.5), (35, 16, 2.5)):
            E(d, cx, cy, r, r)
    hair = m(hair_fn)
    pony = m(lambda d: (E(d, 31.5, 31, 3, 7.5), E(d, 30.5, 37, 2.5, 3)))
    ear = m(lambda d: E(d, 30, 23.5, 3.5, 6.5))
    face = m(lambda d: d.polygon(FACE, fill=255))
    neck = m(lambda d: d.polygon(NECK, fill=255))
    # nacimiento del pelo: frente minima, baja hacia la izquierda
    hl = 18 + (26 - xx) * (5 / 17)
    skin = (face & (yy >= hl)) | ear | neck
    hair_all = (hair | pony) & ~skin
    bgm = ~(hair_all | skin)
    img = skin.copy()
    img |= hair_all & dil(bgm)                     # contorno blanco del pelo
    im = Image.fromarray((img * 255).astype('uint8')); d = ImageDraw.Draw(im)
    P = lambda pts, c=0: [d.point(p, c) for p in pts]
    # rizos
    for x, y in ((8, 7), (14, 5), (21, 5), (27, 7), (11, 11), (18, 10), (25, 11), (31, 11),
                 (6, 15), (14, 15), (21, 14), (3, 22), (31, 33)):
        for dx, dy in ((0, 1), (1, 0), (2, 0), (3, 1)):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and hair_all[Y, X]: d.point((X, Y), 255)
    # oreja: separacion con la cara + pabellon interior
    P([(27, 18), (27, 19), (26, 20), (26, 21), (26, 22), (26, 23), (26, 24), (26, 25), (26, 26), (26, 27), (27, 28), (27, 29)])
    P([(29, 20), (30, 20), (31, 21), (31, 22), (31, 23), (31, 24), (30, 25), (29, 26), (29, 27)])
    # ceja derecha: gruesa y arqueada (sube hacia fuera)
    P([(18, 20), (19, 20), (20, 20), (21, 20), (22, 20), (23, 20),
       (16, 21), (17, 21), (18, 21), (19, 21), (20, 21), (21, 21), (22, 21), (23, 21), (24, 21),
       (15, 22), (16, 22), (17, 22), (14, 23)])
    # ceja izquierda: mas baja
    P([(10, 23), (11, 23), (12, 23), (9, 24), (10, 24), (11, 24), (12, 24), (13, 24), (8, 25)])
    # ojo derecho: almendra negra con brillo
    P([(17, 24), (18, 24), (19, 24), (20, 24), (21, 24), (22, 23), (18, 25), (19, 25), (20, 25), (21, 25)])
    P([(19, 24)], 255)
    # ojo izquierdo
    P([(9, 27), (10, 27), (11, 27), (12, 27), (13, 26), (10, 28), (11, 28), (12, 28)])
    P([(11, 27)], 255)
    # bolsas bajo los ojos
    P([(18, 27), (19, 27), (20, 27), (21, 26)]); P([(9, 30), (10, 30)])
    # nariz larguisima: lados
    P([(15, 25), (15, 26), (14, 27), (14, 28), (14, 29), (13, 30), (13, 31), (13, 32), (12, 33), (12, 34), (12, 35), (11, 36), (11, 37)])
    P([(17, 26), (17, 27), (17, 28), (18, 29), (18, 30), (18, 31), (19, 32), (19, 33), (19, 34), (20, 35)])
    # punta bulbosa y fosa nasal
    P([(11, 38), (11, 39), (12, 40), (13, 41), (14, 42), (15, 42), (16, 42), (17, 41), (18, 40), (19, 39), (20, 38), (20, 37), (20, 36)])
    P([(16, 39), (17, 39), (17, 38)])
    # pliegue de la mejilla izquierda
    P([(10, 31), (10, 32)])
    # sonrisa ancha con dientes (a la derecha de la nariz, comisura alta)
    P([(26, 29), (26, 30), (25, 31), (24, 32), (23, 32), (22, 33), (21, 33)])          # labio superior
    P([(26, 31), (26, 32), (25, 33), (25, 34), (24, 35), (23, 36), (22, 36), (21, 36), (21, 35), (21, 34)])  # labio inferior
    P([(22, 34), (23, 34), (24, 34), (23, 33), (24, 33), (25, 32), (22, 35), (23, 35), (24, 33)], 255)  # dientes
    P([(23, 35), (24, 34)] if False else [(22, 35)])
    # pliegue junto a la boca
    P([(26, 28), (27, 29)]) if False else None
    # mandibula / menton
    P([(26, 38), (25, 39), (24, 40), (23, 41), (22, 42), (21, 43), (20, 44), (19, 45), (18, 45)])
    P([(15, 44), (16, 45)])
    return np.array(im) > 0

if __name__ == '__main__':
    h = build()
    big = Image.fromarray((h * 255).astype('uint8')).resize((W * 10, H * 10), Image.NEAREST).convert('RGB')
    big.save('head4.png')
