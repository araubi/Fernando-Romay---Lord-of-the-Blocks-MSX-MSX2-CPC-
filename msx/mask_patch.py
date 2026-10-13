"""MSX2: la mascara de cada fotograma de jugador borra el fondo bajo toda la silueta (no solo bajo el
relleno blanco original), para que la cancha quede siempre detras del jugador.
Silueta = pixeles no transparentes de las clases de color (colorize.F)."""
from colorize import F
from sprites import entry

def read_rows(F2, i):
    a = entry(i) - 0x415A
    h, w = F2[a], F2[a + 1]; hw = w // 2; a += 2
    return a, h, w, hw

def apply(F1, F2, F3):
    changed = 0; bad = 0
    for i, cls in F.items():
        a, h, w, hw = read_rows(F2, i)
        if hw != 3 or h != len(cls): bad += 1; continue
        for y in range(h):
            r = a + y * w
            for x in range(24):
                ch = cls[y][x]
                d = F2[r + x // 8] & (0x80 >> (x % 8))
                if ch not in '.#' and not d:
                    if F2[r + hw + x // 8] & (0x80 >> (x % 8)):
                        F2[r + hw + x // 8] &= ~(0x80 >> (x % 8)) & 255; changed += 1
    print('mask_patch: pixeles de silueta que ahora borran el fondo', changed, 'fotogramas no tratados', bad)
