"""Utilidades de pantalla CPC modo 1: memoria <-> matriz de tintas (200x320)."""
import numpy as np
def line_addr(y): return 0xC000 + (y >> 3) * 80 + (y & 7) * 0x800
def decode(ram, lines=range(200)):
    P = np.zeros((200, 320), np.uint8)
    for y in lines:
        a = line_addr(y)
        b = np.frombuffer(bytes(ram[a:a + 80]), np.uint8)
        for k in range(4):
            P[y, k::4] = ((b >> (7 - k)) & 1) | (((b >> (3 - k)) & 1) << 1)
    return P
def enc_row(p):
    """p: tintas (multiplo de 4) -> bytes"""
    p = np.asarray(p, np.uint8).reshape(-1, 4); out = np.zeros(len(p), np.uint8)
    for k in range(4):
        out |= ((p[:, k] & 1) << (7 - k)) | (((p[:, k] >> 1) & 1) << (3 - k))
    return bytes(out)
PAL = [(0, 0, 255), (0, 0, 0), (255, 255, 255), (255, 128, 128)]
def to_img(P, scale=1, pal=None, court=None):
    from PIL import Image
    pal = np.array(pal or PAL, np.uint8)
    img = pal[P]
    if court:   # (y0,y1): tinta 0 naranja
        y0, y1 = court; sub = img[y0:y1]; m = P[y0:y1] == 0; sub[m] = (255, 128, 0)
    im = Image.fromarray(img)
    return im.resize((320 * scale * 2 // 2 * 1, 200 * scale)) if scale != 1 else im
def decode_buf(mem, base, rows=104, width=64):
    P = np.zeros((rows, width * 4), np.uint8)
    for y in range(rows):
        b = np.frombuffer(bytes(mem[base + width * y:base + width * (y + 1)]), np.uint8)
        for k in range(4):
            P[y, k::4] = ((b >> (7 - k)) & 1) | (((b >> (3 - k)) & 1) << 1)
    return P
def big(P, s=4, court=None, path=None):
    from PIL import Image
    im = to_img(P, court=court)
    im = im.resize((im.width * s, im.height * s), Image.NEAREST)
    if path: im.save(path)
    return im
