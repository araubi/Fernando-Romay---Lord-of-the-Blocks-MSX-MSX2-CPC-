"""Cancha de la version MSX2 (la del usuario con el logo de Los Angeles 84) en el bitmap de 1 bit del MSX1.
Filas de pantalla 72-119 (filas 64-111 del bitmap de B498h), colores de siempre (tinta negra sobre azul claro):
lineas y logo -> tinta; parquet -> fondo; zonas verdes de dentro (zonas, circulo) -> tramado al 50%
(como las zonas del MSX1); lo verde de fuera de la cancha -> tinta solida (como en el MSX1)."""
import numpy as np
from scipy import ndimage
from court import court_bits, put_bits

Y0 = 72                      # primera fila de pantalla que se sustituye (linea de banda de arriba)
ROW0 = Y0 - 8                # fila del bitmap


def msx2_court():
    import user_art, la84
    return la84.draw(user_art.D['cancha'])           # 64 x 256, filas de pantalla 56-119


def bits_from(c):
    sub = c[Y0 - 56:]                                  # filas 72-119
    h, w = sub.shape
    green = sub == 6
    # lineas de fondo de la cancha (diagonales): recta ajustada a los puntos blancos de cada lado
    ys, xs = np.nonzero(sub == 15)
    L = np.polyfit(ys[xs < 32], xs[xs < 32], 1)
    R = np.polyfit(ys[xs > 223], xs[xs > 223], 1)
    yy0, xx0 = np.mgrid[0:h, 0:w]
    outside = green & ((xx0 < np.polyval(L, yy0) - 0.5) | (xx0 > np.polyval(R, yy0) + 0.5))
    yy, xx = np.mgrid[0:h, 0:w]
    yy = yy + Y0
    out = np.zeros((h, w), bool)
    out |= (sub == 15) | (sub == 1)
    out |= outside
    out |= green & ~outside & ((xx + yy) % 2 == 1)
    return out


def apply(F1, F2, F3):
    b = court_bits(F3)
    b[ROW0:] = bits_from(msx2_court())
    put_bits(F3, b)
