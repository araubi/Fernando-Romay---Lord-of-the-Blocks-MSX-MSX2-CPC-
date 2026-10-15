"""Cabezas (barba de Itu, pelo/nariz de Romay) desde las del MSX1 final. Se normaliza el dibujo:
todas las cabezas en una ventana de 16 px que empieza en x=4 de la pieza de 24 px del MSX y el juego
las desplaza siempre +2 unidades (4 px). Asi se pueden intercambiar entre jugadores."""
import frames
HEADS = [0x0A, 0x0B, 0x16, 0x17, 0x22, 0x23, 0x2E, 0x2F]
MSXF = '/home/claude/cpc/msxfin_ram.bin'
COL = {'.': 0, '#': 1, 'o': 3}
def pack(rows):
    out = bytearray()
    for row in rows:
        for b in range(len(row) // 4):
            v = 0
            for k in range(4):
                p = row[b * 4 + k]
                v |= ((p & 1) << (7 - k)) | (((p >> 1) & 1) << (3 - k))
            out.append(v)
    return bytes(out)
def head_rows(i, src=None):
    M = frames.msx_frames(src or open(MSXF, 'rb').read(), n=75)
    rows = M[i][1]
    out = []
    for r in rows:
        assert all(ch == '.' for ch in r[:4] + r[20:]), (i, r)
        out.append([COL[ch] for ch in r[4:20]])
    return out
def entry(im, i):
    p = im.rd(0x66F4 + 2 * i, 2); return 0x32C8 + (p[0] | p[1] << 8)
# Desplazamiento de las cabezas (unidades de 2 px) como en el CPC original respecto al MSX:
# todas +2, salvo las de frente (22h/23h) +1, y en la segunda ruta (147Ch) tambien las de perfil
# hacia la derecha (16h/17h) +1.
CODE = """
  org 1345h
  ld a,0Ah
  bit 2,(ix-1)
  jr nz,hd_1
  ld a,22h
  bit 1,(ix-1)
  jr z,hd_add
  inc h
  jp 1371h
hd_1:
  bit 3,(ix-1)
  jr z,hd_done
hd_add:
  add a,0Ch
hd_done:
  inc h
  inc h
  jp 1371h
"""
CODE2 = """
  org 147Ch
  ld a,0Ah
  bit 2,(ix-1)
  jr z,h2_1
  bit 3,(ix-1)
  jr z,h2_3
  add a,0Ch
  jr h2_one
h2_1:
  add a,18h
  bit 1,(ix-1)
  jr nz,h2_one
  add a,0Ch
h2_3:
  inc h
h2_one:
  inc h
  jp 14A8h
"""
# 13FAh (la cabeza se gira hacia el rival): como en el MSX, sin los ajustes de x del CPC (que
# compensaban el desplazamiento de los datos antiguos). Si pasa de frente (+1) a perfil (+2), +1.
CODE3 = """
  org 142Dh
  bit 2,(ix-1)
  ret nz
  bit 1,(ix-1)
  jr z,145Dh
  inc h
  bit 0,(ix+1)
  ret z
  dec l
  ret
"""
def apply(im):
    from asm import assemble
    for i in HEADS:
        e = entry(im, i)
        data = bytes([16, 4]) + pack(head_rows(i))
        if im.rd(e, 2) == bytes([16, 4]):
            im.poke(e, data)
        else:
            assert im.rd(e, 1) == bytes([16]), (hex(i), im.rd(e, 2))
            L = im.place('head%02X' % i, 'HD%02X:\n db %s' % (i, ','.join(str(b) for b in data)))
            off = L['HD%02X' % i] - 0x32C8
            im.poke(0x66F4 + 2 * i, [off & 255, off >> 8])
            w = im.rd(e + 1, 1)[0]
            im.free.append([e, e + 2 + 16 * w])      # el hueco de la cabeza antigua queda libre
    code, _, _ = assemble(CODE, 0)
    assert 0x1345 + len(code) <= 0x1371
    im.poke(0x1345, code, [0x3E, 0x0A])
    code, _, _ = assemble(CODE2, 0)
    assert 0x147C + len(code) <= 0x14A8
    im.poke(0x147C, code, [0x3E, 0x0A])
    code, _, _ = assemble(CODE3, 0)
    assert 0x142D + len(code) <= 0x145D
    im.poke(0x142D, code, [0xDD, 0xCB, 0xFF, 0x56])
