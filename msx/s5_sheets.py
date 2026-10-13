"""Plantillas PNG para que el usuario retoque los graficos de la version SCREEN 5 (y su lectura).
Cada plantilla: paneles a escala x4 (1 pixel del MSX = bloque de 4x4) y la paleta de 16 colores.
La lectura toma el centro de cada bloque y lo ajusta al color de la paleta mas cercano."""
import numpy as np, pickle
from PIL import Image, ImageDraw
import s5_assets as SA

S = 4
TRANSP = (255, 0, 255)          # magenta = transparente (solo en las piezas animadas)
MARGIN = 16
TITLE_H = 18

def rgb(i): return SA.rgb8(SA.PAL[i])

def legend(d, x, y):
    d.text((x, y), 'PALETA (solo estos 16 colores; el 0 y el 1 son el mismo negro):', fill=(255, 255, 255))
    y += 14
    for i in range(16):
        X = x + (i % 8) * 92; Y = y + (i // 8) * 26
        d.rectangle([X, Y, X + 20, Y + 20], fill=rgb(i), outline=(128, 128, 128))
        r, g, b = SA.PAL[i]
        d.text((X + 25, Y + 4), '%d  %d%d%d' % (i, r, g, b), fill=(255, 255, 255))
    return y + 56

def paste(im, arr, x, y, transp=False):
    a = np.zeros(arr.shape + (3,), np.uint8)
    for i in range(16): a[arr == i] = rgb(i)
    if transp: a[arr == 0] = TRANSP
    big = Image.fromarray(a).resize((arr.shape[1] * S, arr.shape[0] * S), Image.NEAREST)
    im.paste(big, (x, y))

def layout(panels, extra_h=0, width=None):
    """panels: [(titulo, arr, transp)] uno debajo de otro -> (img, posiciones)"""
    W = width or max(MARGIN * 2 + p[1].shape[1] * S for p in panels)
    W = max(W, 780)
    H = MARGIN + sum(TITLE_H + p[1].shape[0] * S + MARGIN for p in panels) + 110 + extra_h
    im = Image.new('RGB', (W, H), (40, 40, 48)); d = ImageDraw.Draw(im)
    y = MARGIN; pos = []
    for t, arr, tr in panels:
        d.text((MARGIN, y), t, fill=(255, 255, 160)); y += TITLE_H
        paste(im, arr, MARGIN, y, tr); pos.append((MARGIN, y)); y += arr.shape[0] * S + MARGIN
    legend(d, MARGIN, y)
    return im, pos, d, y

# ---------------------------------------------------------------------------------------------
# zonas (coordenadas de pantalla)
CANCHA = (0, 56, 256, 120)       # x0, y0, x1, y1
PUBLICO = (32, 8, 224, 56)
CAN_IZQ = (0, 8, 32, 56)
CAN_DER = (224, 8, 256, 56)
MARCADOR = (0, 120, 256, 192)
# celdas que dibuja el propio juego durante el partido (fila, col0, col1 inclusive)
SB_DYN = [(15, 0, 31), (16, 1, 12), (16, 20, 31), (18, 1, 11), (18, 20, 30), (20, 1, 11), (20, 14, 17), (20, 20, 30)]

def crop(a, r): x0, y0, x1, y1 = r; return a[y0:y1, x0:x1]

def export(P, bg, outdir):
    from court import court_bits
    f3 = P.F['f3'][3]
    bits = court_bits(f3)
    cl, cr = SA.cheer_images(f3, bits, bg)
    files = {}
    # 1. cancha
    im, pos, d, y = layout([('CANCHA (cartel y pista, y 56-119). Retoca libremente: es el fondo.', crop(bg, CANCHA), False)])
    files['cancha'] = im
    # 2. publico normal + levantado
    pub = crop(bg, PUBLICO).copy()
    lev = pub.copy()
    for img, x0 in ((cl, 40), (cr, 128)):
        lev[16 - 8:48 - 8, x0 - 32:x0 - 32 + 88] = img
    im, pos, d, y = layout([('PUBLICO normal (fondo, x 32-223, y 8-55)', pub, False),
                            ('PUBLICO animado: solo cuentan los dos rectangulos marcados (88x32 cada uno)', lev, False)])
    x, yy = pos[1]
    for x0 in (40, 128):
        X = x + (x0 - 32) * S; Y = yy + 8 * S
        d.rectangle([X - 1, Y - 1, X + 88 * S, Y + 32 * S], outline=(255, 255, 0))
    files['publico'] = im
    # 3. marcador + guia
    sbimg, ck = SA.sb_prerender()
    guide = sbimg.copy()
    im, pos, d, y = layout([('MARCADOR (y 120-191). El marco y los adornos son tuyos.', sbimg, False),
                            ('GUIA: lo recuadrado lo escribe el juego en cada partido (nombres, tanteo, reloj, faltas, barras)', guide, False)])
    x, yy = pos[1]
    for r, c0, c1 in SB_DYN:
        d.rectangle([x + c0 * 8 * S, yy + (r - 15) * 8 * S, x + (c1 + 1) * 8 * S - 1, yy + (r - 14) * 8 * S - 1], outline=(255, 0, 255), width=2)
    files['marcador'] = im
    # 4. canastas: fondo + 5 fotogramas por lado
    hoops = SA.hoop_images(P, SA.mock())
    W = 780
    panels = [('CANASTA IZQUIERDA: fondo (x 0-31, y 8-55)', crop(bg, CAN_IZQ), False),
              ('CANASTA DERECHA: fondo (x 224-255, y 8-55)', crop(bg, CAN_DER), False)]
    im, pos, d, y = layout(panels, extra_h=2 * (TITLE_H + 24 * S + MARGIN) + 40)
    # fotogramas en filas (magenta = transparente), justo encima de la paleta: se rehace la imagen
    H = im.height
    im2 = Image.new('RGB', (W + 300, H), (40, 40, 48)); d = ImageDraw.Draw(im2)
    y = MARGIN; fpos = {}
    for t, arr, tr in panels:
        d.text((MARGIN, y), t, fill=(255, 255, 160)); y += TITLE_H
        paste(im2, arr, MARGIN, y); y += arr.shape[0] * S + MARGIN
    for side, base in (('izquierda', 0x3E), ('derecha', 0x43)):
        d.text((MARGIN, y), 'Red %s: 5 fotogramas de 24x24 (magenta = transparente); se dibujan en x=%d, y=32' %
               (side, 8 if base == 0x3E else 224), fill=(255, 255, 160)); y += TITLE_H
        for k in range(5):
            X = MARGIN + k * (24 * S + 12)
            paste(im2, hoops[base + k], X, y, True); fpos[base + k] = (X, y)
        y += 24 * S + MARGIN
    legend(d, MARGIN, y)
    files['canastas'] = im2
    for n, im in files.items(): im.save('%s/MSX2_S5_%s.png' % (outdir, n))
    return files


def export_pres(outdir):
    """presentacion: imagen fija + fotogramas de balon, cabeza y mano (ya coloreados)"""
    import pres_color as PC
    pic, frames = PC.build()
    panels = [('PRESENTACION (imagen completa, 256x192)', pic, False)]
    im, pos, d, y = layout(panels, extra_h=TITLE_H * 3 + 56 * S + 32 * S + 24 * S + 3 * MARGIN)
    im2 = Image.new('RGB', (max(im.width, MARGIN * 2 + 8 * (32 * S + 12)), im.height), (40, 40, 48)); d = ImageDraw.Draw(im2)
    y = MARGIN
    d.text((MARGIN, y), panels[0][0], fill=(255, 255, 160)); y += TITLE_H
    paste(im2, pic, MARGIN, y); y += pic.shape[0] * S + MARGIN
    for title, keys, h in (('CABEZA: 8 fotogramas de 32x56 (x 48, y 8)', PC.HEADS, 56),
                           ('BALON: 3 fotogramas de 32x32 (x 8, y 0)', PC.BALLS, 32),
                           ('MANO: 4 fotogramas de 24x24 (x 56, y 80)', PC.HANDS_ALL, 24)):
        d.text((MARGIN, y), title, fill=(255, 255, 160)); y += TITLE_H
        x = MARGIN
        for k in keys:
            a = frames[k][4]; paste(im2, a, x, y); x += a.shape[1] * S + 12
        y += h * S + MARGIN
    legend(d, MARGIN, y)
    im2.save('%s/MSX2_S5_presentacion.png' % outdir)
    return im2
