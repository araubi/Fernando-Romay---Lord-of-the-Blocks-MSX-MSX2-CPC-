"""Coloreado de la presentacion (Romay con piel) para la version SCREEN 5."""
import pickle, numpy as np
from scipy import ndimage
import s5_assets as SA

SKIN, WHITE, BLACK = 2, 15, 1
# semillas (x, y) de las zonas de piel en la imagen compuesta (estatica + primer fotograma de cada parte)
SEEDS = [(59, 46), (18, 51), (8, 56), (13, 56), (10, 60), (20, 60), (40, 64), (36, 82), (85, 66), (72, 86),
         (45, 128), (68, 130), (56, 146), (53, 148)]
HANDS = (0xCC0A, 0xCC54, 0xCC9E)
BALL = 9          # rojo del balon -> naranja

def load():
    return pickle.load(open('/home/claude/w/pres_cap.pkl', 'rb'))

def composite(d, keys=(0xC39A, 0xC5E0, 0xCBC0)):
    st = d['static'].copy()
    for k in keys:
        y, c, h, w, a = d['frames'][k]; st[y:y + h, c * 8:c * 8 + w * 8] = a
    return st

def skin_mask(img):
    lab, n = ndimage.label(img == 15)
    m = np.zeros(img.shape, bool)
    for x, y in SEEDS:
        if lab[y, x]: m |= lab == lab[y, x]
    return m

def colorize(img, base):
    """img: G2 (indices TMS) ; base: mascara de piel de referencia -> indices de la paleta S5"""
    lut = SA.g2lut()
    out = np.array(lut, np.uint8)[img]
    out[img == 8] = BALL
    lab, n = ndimage.label(img == 15)
    near = ndimage.binary_dilation(base, iterations=1)
    for i in range(1, n + 1):
        c = lab == i
        if (c & near).sum() * 2 > c.sum(): out[c] = SKIN
    return out

def build():
    d = load()
    comp = composite(d)
    base = skin_mask(comp)
    pic = colorize(d['static'], base)
    # las partes animadas sobre la imagen (cada fotograma con la mascara de su sitio)
    frames = {}
    for k, (y, c, h, w, a) in d['frames'].items():
        sub = d['static'].copy(); sub[y:y + h, c * 8:c * 8 + w * 8] = a
        fa = colorize(sub, base)[y:y + h, c * 8:c * 8 + w * 8]
        if k in HANDS:          # dedos pegados a la camiseta: frontera fija
            for yy in range(min(h, 18)):
                x0 = 10 if yy < 10 else 8
                row = a[yy]; fa[yy, x0:][row[x0:] == 15] = SKIN
        frames[k] = (y, c, h, w, fa)
    # la imagen inicial ya con el primer fotograma de cada parte
    for k in (0xC39A, 0xC5E0, 0xCBC0):
        y, c, h, w, a = frames[k]; pic[y:y + h, c * 8:c * 8 + w * 8] = a
    import user_art
    if user_art.D:
        pic = user_art.D['pic'].copy()
        for k, a in user_art.D['frames'].items():
            y, c, h, w, _ = frames[k]; frames[k] = (y, c, h, w, a)
    return pic, frames

if __name__ == '__main__':
    from PIL import Image
    pic, frames = build()
    rgb = np.array([SA.rgb8(SA.PAL[i]) for i in range(16)], np.uint8)
    Image.fromarray(rgb[pic]).resize((768, 576), Image.NEAREST).save('/tmp/claude-0/prescol.png')
    ks = sorted(frames, key=lambda k: (frames[k][0], k))
    S = Image.new('RGB', (sum(frames[k][3] * 8 * 3 + 6 for k in ks), 56 * 3), (60, 60, 60)); x = 0
    for k in ks:
        a = frames[k][4]; S.paste(Image.fromarray(rgb[a]).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST), (x, 0)); x += a.shape[1] * 3 + 6
    S.save('/tmp/claude-0/prescolf.png')

# ---------------------------------------------------------------------------------------------
HEADS = [0xC5E0, 0xC6C2, 0xC7A4, 0xC886, 0xC968, 0xCA4A, 0xCB2C, 0xCC0E]
BALLS = [0xC39A, 0xC41C, 0xC49E]
HANDS_ALL = [0xCBC0, 0xCC0A, 0xCC54, 0xCC9E]
STRIP_H = 88

def strip(frames):
    """fotogramas en una tira de 256 x 88 (pagina 1, y 256..) -> (tira, {src: (x, y)})"""
    s = np.zeros((STRIP_H, 256), np.uint8); pos = {}
    for i, k in enumerate(HEADS): pos[k] = (i * 32, 0)
    for i, k in enumerate(BALLS): pos[k] = (i * 32, 56)
    for i, k in enumerate(HANDS_ALL): pos[k] = (96 + i * 24, 56)
    for k, (x, y) in pos.items():
        a = frames[k][4]; s[y:y + a.shape[0], x:x + a.shape[1]] = a
    return s, pos

def pack(a):
    return bytes(((a[:, 0::2] << 4) | a[:, 1::2]).astype(np.uint8).flatten())

def rle(data):
    out = bytearray(); i = 0; n = len(data)
    while i < n:
        j = i
        while j < n and j - i < 127 and data[j] == data[i]: j += 1
        if j - i >= 3:
            out += bytes([0x80 | (j - i), data[i]]); i = j; continue
        k = i; lit = bytearray()
        while k < n and len(lit) < 127:
            if k + 2 < n and data[k] == data[k + 1] == data[k + 2]: break
            lit.append(data[k]); k += 1
        out += bytes([len(lit)]) + lit; i = k
    return bytes(out + b'\0')

def unrle(b):
    out = bytearray(); i = 0
    while b[i]:
        c = b[i]; i += 1
        if c & 0x80: out += bytes([b[i]]) * (c & 0x7F); i += 1
        else: out += b[i:i + c]; i += c
    return bytes(out)

def streams():
    pic, frames = build()
    s, pos = strip(frames)
    A, B, C = pack(pic[:128]), pack(pic[128:]), pack(s)
    return [rle(A), rle(B), rle(C)], pos, frames
