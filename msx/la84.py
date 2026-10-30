"""Logo de Los Angeles 84 (estrellas en movimiento + aros) en blanco sobre la cancha, por debajo
del circulo central (que se dibuja encima) y entre las dos lineas de tres."""
import numpy as np
from PIL import Image

FLOOR, GREEN, WHITE = 3, 6, 15
CX = 128                      # linea central
X0, X1 = 81, 173              # zona libre entre los arcos de tres (columnas)
TOP, BOT = 17, 62             # filas de parquet (cancha de 64 filas: lineas de banda en 16 y 63)


def _mask():
    im = np.array(Image.open('la84_logo.png').convert('RGB')).astype(int)
    return im[:, :, 2] - im[:, :, 1] > 60


def _bands(p):
    rows = p.sum(1) > 0
    out, s = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and s is None: s = y
        if not v and s is not None: out.append((s, y - 1)); s = None
    return out


def draw(c):
    c = c.copy()
    # limpiar el logo anterior (todo entre los arcos salvo la linea central)
    z = c[TOP:BOT + 1, X0:X1 + 1]
    z[(z == WHITE) | (z == GREEN)] = FLOOR
    p = _mask()
    bands = _bands(p)
    stripes, rings = bands[:-1], bands[-1]
    xs = np.nonzero(p[:rings[0] - 5].any(0))[0]
    ox0, ox1 = xs.min(), xs.max() + 1
    W = 91                                    # ancho del logo en pixeles
    s = W / (ox1 - ox0)
    lx0 = CX - W // 2
    # estrellas: una fila por franja, separadas por una fila de parquet
    y0 = 19
    st = np.zeros((2 * len(stripes), W), bool)
    for k, (a, b) in enumerate(stripes):
        row = p[a:b + 1].mean(0)               # cobertura media de la franja
        for x in range(W):
            u0 = ox0 + x / s; u1 = ox0 + (x + 1) / s
            if row[int(u0):max(int(u0) + 1, int(u1))].mean() >= 0.5:
                st[2 * k, x] = True
    # las estrellas, centradas de verdad en la linea central (lo dibujado no es simetrico en el logo)
    xs = np.nonzero(st.any(0))[0]
    sx = int(round(CX + 0.5 - (lx0 + (xs.min() + xs.max() + 1) / 2)))
    for y, x in zip(*np.nonzero(st)):
        c[y0 + y, lx0 + x + sx] = WHITE
    # aros: elipses (perspectiva de la cancha), centros del logo oficial
    ry_k = 0.62
    top_c = [(203, 417), (333, 417), (462, 417)]
    bot_c = [(268, 466), (397, 466)]
    R = 52.5
    rx = R * s; ry = rx * ry_k
    cy0 = y0 + 2 * (len(stripes) - 1) + 3 + ry
    for (ux, uy) in top_c + bot_c:
        ex = lx0 + (ux - ox0) * s
        ey = cy0 + (uy - 417) * s * ry_k
        for yy in range(int(ey - ry - 2), int(ey + ry + 3)):
            for xx in range(int(ex - rx - 2), int(ex + rx + 3)):
                # distancia normalizada al anillo, en pixeles de pantalla
                dx = (xx + 0.5 - ex) / rx; dy = (yy + 0.5 - ey) / ry
                r = np.hypot(dx, dy)
                if r == 0: continue
                # grosor de ~1 pixel medido a lo largo de la direccion radial
                g = 1.0 / np.hypot(dx * rx, dy * ry) * r
                if abs(r - 1) <= 0.55 * g * r:
                    c[yy, xx] = WHITE
    # circulo central verde con contorno blanco, encima del logo
    cy, crx, cry = 36.5, 17.0, 7.0
    for yy in range(28, 46):
        for xx in range(CX - 20, CX + 21):
            d = ((xx + 0.5 - (CX + 0.5)) / crx) ** 2 + ((yy + 0.5 - cy) / cry) ** 2
            do = ((xx + 0.5 - (CX + 0.5)) / (crx + 1)) ** 2 + ((yy + 0.5 - cy) / (cry + 1)) ** 2
            if d <= 1: c[yy, xx] = GREEN
            elif do <= 1: c[yy, xx] = WHITE
    c[TOP:BOT + 1, CX] = WHITE              # linea central encima de todo
    return c
