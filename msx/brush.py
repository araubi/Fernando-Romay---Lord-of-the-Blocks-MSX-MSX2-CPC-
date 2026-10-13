"""Caligrafia de pincel/plumilla para 'Lord of the blocks' al estilo del 'Executive' original.
Cada letra es una lista de trazos (curvas Catmull-Rom) en pixeles de destino; se dibujan con
una plumilla biselada (gruesos y finos) a 8x, se inclinan y se reducen a 1 bit."""
import numpy as np
from PIL import Image, ImageDraw

SC = 8

def catmull(pts, n=10):
    if len(pts) < 3: return pts
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, P[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(pts[-1]); return out

def nib(d, pts, w, ang, ox, oy, thin=0.9):
    c, s = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    nx, ny = c * w / 2, -s * w / 2
    P = [((ox + x) * SC, (oy + y) * SC) for x, y in catmull(pts)]
    for (x1, y1), (x2, y2) in zip(P, P[1:]):
        d.polygon([(x1 - nx * SC, y1 - ny * SC), (x1 + nx * SC, y1 + ny * SC), (x2 + nx * SC, y2 + ny * SC), (x2 - nx * SC, y2 - ny * SC)], fill=255)
        r = thin * SC / 2
        d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=255)

# glifos grandes: linea base y=0, altura x 12, ascendentes 24 (coordenadas antes de inclinar)
BIG = {
 'L': (17, [[(9, -22), (6, -24), (4, -21), (3, -12), (2, -4), (1, -1)],
            [(-2, 2), (1, 0), (6, -1), (12, -1), (17, 1)]]),
 'o': (11, [[(6, -12), (2, -9), (1, -4), (3, 0), (7, -1), (10, -6), (9, -11), (6, -12)]]),
 'r': (9,  [[(1, -12), (1, -6), (1, 0)], [(1, -7), (3, -11), (6, -12), (9, -10)]]),
 'd': (13, [[(8, -11), (4, -12), (1, -8), (1, -3), (4, 0), (8, -3), (9, -8)], [(11, -25), (10, -12), (9, -3), (10, 0), (13, 0)]]),
 'b': (12, [[(3, -25), (2, -12), (1, 0)], [(1, -6), (4, -11), (8, -12), (11, -8), (10, -3), (6, 0), (2, -1)]]),
 'l': (6,  [[(4, -25), (3, -14), (2, -4), (3, 0), (6, 0)]]),
 'c': (10, [[(10, -10), (7, -12), (3, -10), (1, -5), (3, 0), (7, 0), (10, -2)]]),
 'k': (12, [[(3, -25), (2, -12), (1, 0)], [(10, -12), (6, -9), (2, -5)], [(4, -6), (7, -2), (9, 0), (12, 0)]]),
 's': (10, [[(10, -11), (7, -12), (3, -11), (2, -8), (5, -6), (8, -5), (9, -2), (6, 0), (1, -1)]]),
}
# glifos pequenos (altura x 7, ascendentes 13)
SMALL = {
 'o': (7, [[(4, -7), (1, -5), (1, -1), (4, 0), (6, -3), (5, -7), (4, -7)]]),
 'f': (6, [[(7, -13), (5, -14), (3, -11), (2, -2), (1, 3), (-1, 4)], [(0, -7), (6, -7)]]),
 't': (5, [[(3, -11), (2, -3), (3, 0), (5, 0)], [(0, -7), (5, -7)]]),
 'h': (7, [[(2, -14), (1, -6), (1, 0)], [(1, -4), (3, -7), (6, -6), (6, -1), (7, 0)]]),
 'e': (6, [[(1, -3), (6, -4), (5, -7), (2, -7), (1, -4), (1, -1), (3, 0), (6, -1)]]),
}

def render(layout, size=(224, 40), shear=0.32, w_big=3.6, w_small=2.2, ang=35, thr=96):
    """layout: lista de (texto, 'big'|'small', x, y_base)"""
    W, H = size
    im = Image.new('L', (W * SC, H * SC), 0); d = ImageDraw.Draw(im)
    for text, kind, x, yb in layout:
        G = BIG if kind == 'big' else SMALL
        wn = w_big if kind == 'big' else w_small
        for ch in text:
            if ch == ' ': x += 4 if kind == 'small' else 7; continue
            adv, strokes = G[ch]
            for st in strokes: nib(d, st, wn, ang, x, yb)
            x += adv + (2 if kind == 'big' else 1.5)
    # inclinacion (cursiva) respecto a la linea base
    yc = 34 * SC
    im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * yc, 0, 1, 0), resample=Image.BICUBIC)
    a = np.asarray(im.resize((W, H), Image.BOX)) > thr
    return a

def preview(a, scale=4):
    return Image.fromarray((a * 255).astype('uint8')).resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST)

if __name__ == '__main__':
    LAY = [('Lord', 'big', 8, 34), ('of the', 'small', 72, 34), ('blocks', 'big', 112, 34)]
    preview(render(LAY)).save('brush.png')
