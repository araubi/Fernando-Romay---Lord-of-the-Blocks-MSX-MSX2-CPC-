"""Pista del MSX2 (con el logo de Los Angeles 84) en los 4 colores del CPC."""
import pickle, numpy as np
from scipy import ndimage
def court_rows():
    c = pickle.load(open('/home/claude/cpc/cancha_msx2.pkl', 'rb'))[16:64]   # filas 56-103 del fondo CPC
    outside = np.zeros(c.shape, bool)
    H = c.shape[0]
    L = []; R = []
    for y in range(H):
        xs = np.nonzero(c[y] == 15)[0]
        if len(xs) and xs.min() < 40: L.append((y, xs.min()))
        if len(xs) and xs.max() > 215: R.append((y, xs.max()))
    def fit(P):
        P = np.array(P, float)
        for _ in range(3):
            k, b = np.polyfit(P[:, 0], P[:, 1], 1)
            r = np.abs(P[:, 1] - (k * P[:, 0] + b))
            P = P[r <= max(1.0, np.median(r) * 2)]
        return k, b
    kl, bl = fit(L); kr, br = fit(R)
    for y in range(H):
        xl = int(round(kl * y + bl)); xr = int(round(kr * y + br))
        outside[y, :xl] = True; outside[y, xr + 1:] = True
    out = np.zeros(c.shape, np.uint8)
    H, W = c.shape
    for y in range(H):
        for x in range(W):
            v = c[y, x]
            if v == 15: out[y, x] = 2
            elif v == 3: out[y, x] = 0
            elif v == 6:
                out[y, x] = 1 if outside[y, x] else (2 if (x + y) % 2 else 0)
            elif v == 1: out[y, x] = 1
            else: out[y, x] = 0
    return out
