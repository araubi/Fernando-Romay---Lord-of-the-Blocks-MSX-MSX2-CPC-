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
    # lineas de fondo (diagonales): el primer / ultimo pixel que no es verde de cada fila, recta ajustada
    # quitando los puntos que se apartan (los tramos de las zonas pegadas al fondo)
    def edge(first):
        ys, xs = [], []
        for y in range(1, h - 1):
            nz = np.nonzero(~green[y])[0]
            if len(nz): ys.append(y); xs.append(nz.min() if first else nz.max())
        ys, xs = np.array(ys), np.array(xs)
        k = (xs < 40) if first else (xs > 215)
        for _ in range(4):
            f = np.polyfit(ys[k], xs[k], 1)
            k = np.abs(np.polyval(f, ys) - xs) <= 1.5
        return f
    L, R = edge(True), edge(False)
    yy0, xx0 = np.mgrid[0:h, 0:w]
    xl = np.round(np.polyval(L, yy0)); xr = np.round(np.polyval(R, yy0))
    outside = (xx0 < xl) | (xx0 > xr)
    yy, xx = np.mgrid[0:h, 0:w]
    yy = yy + Y0
    inside = ~outside
    out = np.zeros((h, w), bool)
    out |= inside & ((sub == 15) | (sub == 1))
    out |= green & inside & ((xx + yy) % 2 == 1)
    # como en el MSX1: fuera tinta solida, un pixel de fondo y la linea de fondo continua
    out |= (xx0 < xl - 1) | (xx0 > xr + 1)
    out &= ~((xx0 == xl - 1) | (xx0 == xr + 1))
    out |= (xx0 == xl) | (xx0 == xr)
    out[0] = True; out[-1] = True                     # lineas de banda (arriba y abajo)
    return out


def apply(F1, F2, F3):
    b = court_bits(F3)
    b[ROW0:] = bits_from(msx2_court())
    put_bits(F3, b)
