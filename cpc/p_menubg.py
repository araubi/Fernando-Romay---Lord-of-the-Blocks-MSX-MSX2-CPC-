"""Fondo del menu de la version MSX1 (montaje del usuario, con el segundo logo de Dinamic corregido):
rotulo FERNANDO/ROMAY con la bandera, (C)NIDAMIC 1987, 'Lord of the blocks' con la estrella y la banda
VERSION sobre fondo cian, con las franjas negras de los lados. La pantalla del MSX (256x192) cabe tal cual
en la de 256x192 del CPC.
- Tintas: 0 cian (fondo), 1 negro; 2 y 3 azul y rojo en el rotulo (lineas 0-87) y blanco y rosa debajo
  (textos y munecos): cambio a media pantalla con las interrupciones (p_raster, MATCH=3).
- Los recuadros, textos y munecos del menu bajan 48 lineas (tabla de lineas desplazada, TSET), asi que
  el recuadro negro queda debajo del rotulo como en el MSX. Ya no se imprimen la cabecera de texto ni el
  copyright (estan en el rotulo).
- Al salir del menu hacia el partido (22B3h) se vuelve a la tabla normal: el marcador (energia) se
  dibuja antes de SETUP.
- El rotulo (96 lineas) va comprimido (lz) en trozos; se descomprime en el bufer y se copia a pantalla."""
import numpy as np, lz, scrmap
ROWS = 96

def graphic():
    mc = np.load('/home/claude/cpc/menu_msx1.npy')     # 192x256: 0 negro, 1 cian, 2 azul, 3 blanco, 4 rojo
    pen = np.array([1, 0, 2, 2, 3], np.uint8)[mc]
    out = bytearray()
    for y in range(ROWS):
        for bx in range(64):
            v = 0
            for k in range(4):
                p = int(pen[y, bx * 4 + k]); v |= ((p & 1) << (7 - k)) | (((p >> 1) & 1) << (3 - k))
            out.append(v)
    edge = bytearray()
    for bx in range(64):
        v = 0
        for k in range(4):
            p = int(pen[188, bx * 4 + k]); v |= ((p & 1) << (7 - k)) | (((p >> 1) & 1) << (3 - k))
        edge.append(v)
    return bytes(out), bytes(edge)

def split(c, maxlen):
    """trozos del flujo lz (en limites de token), cada uno terminado en 0"""
    toks = []; i = 0
    while c[i]:
        k = c[i]; n = 1 + (k if k < 128 else 1); toks.append(c[i:i + n]); i += n
    parts = []; cur = b''
    for t in toks:
        if len(cur) + len(t) + 1 > maxlen: parts.append(cur + b'\0'); cur = b''
        cur += t
    parts.append(cur + b'\0')
    return parts

def apply(im):
    g, edge = graphic()
    z = lz.compress(g)
    assert lz.decompress(z) == g
    # primero trozos de 64 bytes en las zonas libres tardias de la pantalla (solo valen para datos que se
    # usan despues de la presentacion), el resto en trozos normales
    late = list(scrmap.FREE_LATE)
    toks = split(z, 1)          # un token por trozo
    toks = [t[:-1] for t in toks]
    parts = []; cur = b''
    for t in toks:
        lim = 64 if len(parts) < len(late) else 440
        if len(cur) + len(t) + 1 > lim: parts.append(cur + b'\0'); cur = b''
        cur += t
    parts.append(cur + b'\0')
    assert b''.join(p[:-1] for p in parts) + b'\0' == z
    im.menubg = (len(g), len(z), len(parts))
    dbs = lambda name, d: name + ':\n' + ''.join('  db ' + ','.join(str(b) for b in d[i:i + 16]) + '\n' for i in range(0, len(d), 16))
    nl = min(len(late), len(parts))
    for k in range(nl):
        a0, a1 = late[k]; assert len(parts[k]) <= a1 - a0
        im.poke(a0, parts[k])
    im.menubg_late = nl
    src = """
; 21C8h: fondo del menu (en lugar de la cabecera de texto); direcciones absolutas
MBG:
  ld de,0A568h
  ld ix,MGP
mg_1:
  ld l,(ix+0)
  ld h,(ix+1)
  ld a,h
  or l
  jr z,mg_2
  call DZ
  inc ix
  inc ix
  jr mg_1
mg_2:
  ld hl,MGE
  ld bc,64
  ldir
  jp MBG2
@@SPLIT@@
MBG2:
  ld hl,0A568h
  ld a,%d
mb_1:
  push af
  call SADR
  ld bc,64
  ldir
  pop af
  inc a
  cp %d
  jr nz,mb_1
mb_2:
  push af
  call SADR
  ld hl,0A568h + %d
  ld bc,64
  ldir
  pop af
  inc a
  cp %d
  jr nz,mb_2
  ld a,%d
  jp TSET
@@SPLIT@@
; 22B3h: al salir del menu al partido, tabla de lineas normal (en lugar de la franja que borraba el
; original bajo el recuadro: con el menu desplazado caeria fuera de la pantalla, y enseguida hay fundido)
MBOX:
  xor a
  jp TSET
@@SPLIT@@
; 2270h: paleta del menu encendida -> cambio de tintas a media pantalla
; (al volver a encender la paleta, por ejemplo al cambiar de nivel, se espera al VSYNC y se ponen ya las
; tintas del rotulo: si no, la parte de arriba saldria un cuadro con blanco y rosa)
MPON:
  ld a,3
  ld (MATCH),a
  ld b,0F5h
mp_1:
  in a,(c)
  rra
  jr nc,mp_1
  call 7581h
  ld bc,7F02h
  out (c),c
  ld a,85
  out (c),a
  inc c
  out (c),c
  ld a,76
  out (c),a
  ret
""" % (scrmap.MENU_Y, scrmap.MENU_Y + ROWS, ROWS * 64, scrmap.Y1, scrmap.MENU_D)
    src += '@@SPLIT@@\n' + dbs('MGE', edge)
    ptrs = ['%d' % late[k][0] for k in range(nl)] + ['MG%d' % k for k in range(nl, len(parts))] + ['0']
    src += '@@SPLIT@@\nMGP:\n' + ''.join('  dw %s\n' % x for x in ptrs)
    for k in range(nl, len(parts)): src += '@@SPLIT@@\n' + dbs('MG%d' % k, parts[k])
    L = im.place_many('menubg', src.split('@@SPLIT@@'))
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x21CE, [0xCD] + w(L['MBG']), [0xCD, 0xBB, 0x10])
    im.poke(0x2265, [0] * 6, [0x21, 0x15, 0x04, 0xCD, 0xBB, 0x10])       # sin copyright
    im.poke(0x226B, [0x3E, 0x13], [0x3E, 0x15])                          # tinta 0: cian
    im.poke(0x2270, [0xCD] + w(L['MPON']), [0xCD, 0x81, 0x75])
    im.poke(0x22B3, [0xCD] + w(L['MBOX']), [0xCD, 0x24, 0x74])
