"""Presentacion del MSX2 (Romay con el balon, logo NIDAMIC) en modo 1 con los 4 colores de la
presentacion del CPC (negro, naranja, blanco, piel). Se rehace la pantalla comprimida de ANIPAN.BIN y
los fotogramas animados (balon 3, cabeza 8, mano 4) del bloque que se copia a A568h."""
import pickle, numpy as np
SRC = pickle.load(open('intro_src.pkl', 'rb'))
CMAP = {1: 0, 9: 1, 15: 2, 2: 3, 4: 2, 7: 2}
OX = 48            # la imagen del MSX2 (256x192) va en x=48 de los 320 px del CPC
def to_cpc(a): return np.vectorize(lambda v: CMAP.get(int(v), 0))(a).astype(np.uint8)
import scrmap
def screen_bytes(img):            # img 200x320 indices 0-3 -> 16 KB de pantalla (C000h), 256x192 (bytes 8-71)
    scr = bytearray(0x4000)
    for y in range(200):
        for bx in range(8, 72):
            v = 0
            for k in range(4):
                p = int(img[y, bx * 4 + k]); v |= ((p & 1) << (7 - k)) | (((p >> 1) & 1) << (3 - k))
            scr[scrmap.addr(y, bx) - 0xC000] = v
    return scr
def rect_bytes(img, x, y, w, h):
    out = bytearray()
    for yy in range(y, y + h):
        for bx in range(x // 4, (x + w) // 4):
            v = 0
            for k in range(4):
                p = int(img[yy, bx * 4 + k]); v |= ((p & 1) << (7 - k)) | (((p >> 1) & 1) << (3 - k))
            out.append(v)
    return bytes(out)
def compress(out_seq):
    """out_seq: bytes en orden de escritura (de la direccion alta a la baja). Devuelve el flujo tal
    como queda en memoria (se lee hacia atras), con el 0 final al principio."""
    toks = []; i = 0; n = len(out_seq); lit = []
    def flush():
        while lit:
            chunk = lit[:65535]; del lit[:65535]
            toks.append(('L', chunk))
    while i < n:
        j = i
        while j < n and out_seq[j] == out_seq[i] and j - i < 65535: j += 1
        if j - i >= 4:
            flush(); toks.append(('R', out_seq[i], j - i)); i = j
        else:
            lit.append(out_seq[i]); i += 1
    flush()
    # cada token, en orden de lectura (direcciones decrecientes): flag, c, [b], datos
    rd = []
    for t in toks:
        if t[0] == 'L':
            cnt = len(t[1]); big = cnt > 255
            rd += [0x05 if big else 0x01, cnt & 255] + ([cnt >> 8] if big else []) + list(t[1])
        else:
            cnt = t[2]; big = cnt > 255
            rd += [0x07 if big else 0x03, cnt & 255] + ([cnt >> 8] if big else []) + [t[1]]
    rd.append(0)
    return bytes(reversed(rd))       # en memoria: el 0 en la direccion mas baja
def check(an, scr):
    m = bytearray(65536); m[0xBFCC:0xBFCC + len(an)] = an
    hl = m[0xBFCD] | m[0xBFCE] << 8; de = 1
    while True:
        a = m[hl]
        if a == 0: break
        hl -= 1; b = 0; c = m[hl]; hl -= 1
        if a & 4: b = m[hl]; hl -= 1
        bc = b << 8 | c
        if not a & 2:
            for _ in range(bc): m[de & 0xFFFF] = m[hl]; hl -= 1; de -= 1
        else:
            for _ in range(bc): m[de & 0xFFFF] = m[hl]; de -= 1
            hl -= 1
    assert bytes(m[0xC000:0x10000]) == bytes(scr), 'la descompresion no coincide'
def picture():
    img = np.zeros((200, 320), np.uint8)
    img[0:192, OX:OX + 256] = to_cpc(SRC['pic'])
    return img
FR = SRC['frames']
BALLS = [0xC39A, 0xC41C, 0xC49E]
HEADS = [0xC5E0, 0xC6C2, 0xC7A4, 0xC886, 0xC968, 0xCA4A, 0xCB2C, 0xCC0E]
HANDS = [0xCBC0, 0xCC0A, 0xCC54, 0xCC9E]
def apply(im):
    img = picture()
    put_frames(im, img)
def finish(im):
    """al final (p_screen): la pantalla de la presentacion, con lo colocado en las zonas libres de la memoria
    de pantalla (im.scr). El flujo comprimido puede pasar de CED8h: el bloque de A568h se copia antes de
    descomprimir, asi que va justo detras del flujo y CARGA lo copia desde ahi."""
    img = picture()
    scr = screen_bytes(img)
    for f0, f1 in scrmap.FREE_EARLY:
        o0, o1 = f0 - 0xC000, f1 - 0xC000
        assert not any(scr[o0:o1])
        scr[o0:o1] = im.scr[o0:o1]
    seq = bytes([0, 0]) + bytes(reversed(scr))          # 0001h, 0000h, FFFFh ... C000h
    stream = compress(seq)
    an = im.an
    start = 0xBFF1
    end = start + len(stream) - 1
    xb = bytes(an[im.xsrc - 0xBFCC:im.xsrc - 0xBFCC + (0xBFB8 - 0xA568)])
    xsrc = end + 1
    assert xsrc + len(xb) <= 0x10000
    head = bytes(an[0:start - 0xBFCC])
    an[:] = head + stream + xb
    assert an[0:3] == bytes([0x21, 0xD8, 0xCE])
    an[1] = end & 255; an[2] = end >> 8
    im.xsrc = xsrc
    im.poke(0x01D8, [0x21, xsrc & 255, xsrc >> 8], [0x21, 0xD9, 0xCE])
    check(bytes(an), scr)
    im.intro_stream = len(stream)
def put_frames(im, img):
    # fotogramas (bloque A568h): balon (56,0) 32x32, cabeza (96,8) 32x56, mano (104,72) 32x32
    def put_frame(idx, x, y, w, h, patch):
        tab = im.rd(0xBA86 + 2 * idx, 2); a = 0xA568 + (tab[0] | tab[1] << 8)
        assert im.rd(a, 2) == bytes([h, w // 4]), (idx, im.rd(a, 2))
        g = img.copy()
        if patch is not None:
            px, py, arr = patch; g[py:py + arr.shape[0], px:px + arr.shape[1]] = to_cpc(arr)
        im.poke(a + 2, rect_bytes(g, x, y, w, h))
    for k, key in enumerate(BALLS): put_frame(k, 56, 0, 32, 32, (OX + 8, 0, FR[key]))
    for k, key in enumerate(HEADS): put_frame(3 + k, 96, 8, 32, 56, (OX + 48, 8, FR[key]))
    for k, key in enumerate(HANDS): put_frame(11 + k, 104, 72, 32, 32, (OX + 56, 80, FR[key]))
