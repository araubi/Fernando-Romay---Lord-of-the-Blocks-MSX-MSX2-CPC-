"""Nueva pantalla del partido (segun el montaje del usuario):
- La pista, las canastas y los jugadores bajan 18 lineas: la fila 0 del bufer va a la linea 42 (antes 24).
  Las coordenadas del juego no cambian; solo cambia la tabla de lineas del volcado (8118h, ver p_raster).
- El publico y la valla suben 13 lineas: el publico (lineas 11-41) queda entero por encima del bufer, asi
  que ni el balon ni los jugadores llegan nunca a su altura (lo que pasa de la fila 0 no se dibuja).
  Se dibuja aparte y solo cambia con la animacion de celebracion, directa a pantalla (al volcar).
- Entre la valla y la pista hay una banda gris de tres escalones (fondo empaquetado, ver p_bgpack).
- Marcador nuevo y mas bajo (lineas 147-180): energia en dos barras de 12 (24 unidades, una mas que
  antes), balon de posesion y personales en la fila de arriba; nombre con letra pequena (5x7, avance 6)
  y puntos en la de abajo; tiempo arriba en el centro y reloj de posesion (30) debajo.
  Los textos del marcador se recolocan en la salida de caracteres (79E2h)."""
import numpy as np
import bg, design, lz, smallfont, scrmap

BG = 0x8B68
CHEER = 0x264A
P5, P6 = 0x31AE, 0x31C0          # tapas de los tableros (2 bytes x 8 lineas), antes en las lineas 16-23


def line_addr(y): return scrmap.vaddr(y)       # columna 0 'virtual' (la 8 es la primera visible)


def old_static(im):
    S = np.full((200, 320), design.BLACK, np.uint8)
    S[24:128, 32:288] = bg.decode(im.rd(BG, 0x1A00))
    for a, x in ((P5, 40), (P6, 272)):
        c, b = im.rd(a, 2)
        S[16:24, x:x + 4 * b] = bg.decode(im.rd(a + 2, c * b), w=b, h=c)
    return S


SRC = """
; ---- 0FFFh: dibujo fijo de la pantalla del partido (en lugar de 8686h) ----
SETUP:
  xor a
  call TSET
  ld a,1
  ld (MATCH),a
  ld a,42
  call SETTAB
  ld hl,SBZ
  ld de,0A568h
  call DZ
  ld hl,0A568h
  ld a,146
  ld b,38
  call BLR
  jp SETUP2
@@SPLIT@@
SETUP2:
  xor a
  ld b,{C0}
  call CLRL
  ld a,181
  ld b,19
  call CLRL
  call CROWDF
  call CREST
  ld de,{P5}+2
  ld hl,{TAB5}
  ld bc,0208h
  call 86BCh
  ld de,{P6}+2
  ld hl,{TAB6}
  ld bc,0208h
  call 86BCh
  xor a
  ld (CHS),a
  ret
@@SPLIT@@
; descompresion LZ (ver lz.py): HL origen, DE destino
DZ:
  ld a,(hl)
  inc hl
  or a
  ret z
  jp m,dz_m
  ld c,a
  ld b,0
  ldir
  jr DZ
dz_m:
  sub 125
  ld c,a
  ld b,0
  ld a,(hl)
  inc hl
  push hl
  cpl
  ld l,a
  ld h,0FFh
  add hl,de
  ldir
  pop hl
  jr DZ
@@SPLIT@@
; A = linea -> DE = direccion de pantalla de la columna 0 del bufer (byte 8)
LADR:
  push hl
  ld l,a
  ld h,0
  add hl,hl
  ld de,7B70h
  add hl,de
  ld e,(hl)
  inc hl
  ld d,(hl)
  ld hl,8
  add hl,de
  ex de,hl
  pop hl
  ret
@@SPLIT@@
; B filas de 64 bytes desde HL a pantalla, desde la linea A
BLR:
  push bc
  call LADR
  ld bc,64
  ldir
  pop bc
  inc a
  djnz BLR
  ret
@@SPLIT@@
; publico (lineas 11-41, fuera del bufer): fila en negro y bordes (izquierda guardada, derecha en espejo)
CROWDF:
  ld hl,EDGES
  ld a,{C0}
cf_1:
  push af
  call LADR
  push hl
  ld h,d
  ld l,e
  inc de
  ld (hl),0F0h
  ld bc,63
  ldir
  pop hl
  jp CROWDF2
@@SPLIT@@
CROWDF2:
  call LADR
  ex de,hl
  ld bc,8
  add hl,bc
  ex de,hl
  push hl
  ld bc,3
  ldir
  pop hl
  ex de,hl
  ld bc,42
  add hl,bc
  ex de,hl
  jp CROWDF3
@@SPLIT@@
CROWDF3:
  ld b,3
  inc hl
  inc hl
cf_2:
  ld a,(hl)
  dec hl
  call MIRB
  ld (de),a
  inc de
  djnz cf_2
  inc hl
  inc hl
  inc hl
  inc hl
  pop af
  inc a
  cp 42
  jp nz,cf_1
  ret
@@SPLIT@@
; las mitades del publico en reposo: filas 0-1 (iguales a la animacion), 2-16 (XC1) y 17-30 (XC2)
CREST:
  ld hl,{CHEER}
  ld bc,0
  ld de,{C0}*256+{C0}+2
  call HALV
  ld hl,{XC1}
  ld de,({C0}+2)*256+{C0}+17
  call HALV
  ld hl,{XC2}
  ld de,({C0}+17)*256+42
  jp HALV
@@SPLIT@@
; byte con los 4 pixeles en orden inverso
MIRB:
  push bc
  ld c,a
  ld b,8
mb_1:
  rr c
  rla
  djnz mb_1
  rlca
  rlca
  rlca
  rlca
  pop bc
  ret
@@SPLIT@@
; las dos mitades del publico desde la linea D hasta la E-1, origen HL (21 bytes por fila, seguidas)
HALV:
  ld a,e
  ld (hv_e+1),a
  ld a,d
hv_1:
  call LADR
  push hl
  ld hl,11
  add hl,de
  ex de,hl
  pop hl
  ld bc,21
  ldir
  jp HALV2
@@SPLIT@@
HALV2:
  ld bc,-21
  add hl,bc
  ld bc,21
  ldir
  inc a
hv_e:
  cp 42
  jp nz,hv_1
  ret
@@SPLIT@@
; 02D6h: antes del volcado, el publico animado (1: animado, 2: se repone)
CHPD:
  ld a,(CHS)
  or a
  jp z,PDUMP
  dec a
  jr nz,cp_2
  ld a,2
  ld (CHS),a
  ld hl,{CHEER}
  ld bc,0
  ld de,{C0}*256+42
  call HALV
  jp PDUMP
cp_2:
  xor a
  ld (CHS),a
  call CREST
  jp PDUMP
@@SPLIT@@
; 2190h: publico animado: todo va directo a pantalla, nada al bufer
CHREC2:
  ld a,1
  ld (CHS),a
  pop hl
  ret
CHS: db 0
@@SPLIT@@
; 1C57h: una unidad de energia. A indice (0-23), C 0Eh encendida / F0h apagada, L 59h izq / 80h dcha
; 12-23 en la barra de arriba (lineas 153-154), 0-11 en la de abajo (157-158); la derecha en espejo
EUNIT:
  ld b,a
  ld a,c
  cp 0F0h
  jr z,eu_1
  ld a,1Eh
  bit 7,l
  jr z,eu_1
  ld a,87h
eu_1:
  ld c,a
  ld a,b
  ld h,153
  sub 12
  jr nc,eu_2
  add a,12
  ld h,157
eu_2:
  bit 7,l
  jr z,eu_3
  cpl
  add a,63
  jr eu_4
eu_3:
  inc a
eu_4:
  jp EUNIT2
@@SPLIT@@
EUNIT2:
  push af
  ld a,h
  call LADR
  pop af
  ld l,a
  ld h,0
  add hl,de
  ld (hl),c
  ld a,h
  add a,8
  ld h,a
  ld (hl),c
  ret
@@SPLIT@@
; 79E2h: salida de caracteres. En el partido, los textos del marcador se recolocan
SBCHR:
  ld e,a
  ld d,0
  ld a,(MATCH)
  or a
  ret z
  push hl
  push bc
  ld hl,SBT
  ld a,(0060h)
  ld b,a
  ld a,(0061h)
  ld c,a
  jp sb_1
@@SPLIT@@
sb_1:
  ld a,(hl)
  or a
  jr z,sb_x
  inc hl
  cp b
  ld a,c
  jr nz,sb_4
  sub (hl)
  inc hl
  cp (hl)
  inc hl
  jr nc,sb_2
  jp SBHIT
sb_4:
  inc hl
  inc hl
sb_2:
  inc hl
  inc hl
  jr sb_1
sb_x:
  pop bc
  pop hl
  ret
@@SPLIT@@
; A = desplazamiento en el campo, HL -> fila nueva (0 letra pequena, FFh no se dibuja), columna nueva
SBHIT:
  ld d,a
  ld a,(hl)
  inc hl
  or a
  jp z,sb_s
  inc a
  jp z,sb_k
  dec a
  ld (0060h),a
  ld a,(hl)
  add a,d
  ld (0061h),a
  ld a,1
  ld (SBSAV),a
  ld a,b
  ld (SBSAV+1),a
  ld a,c
  ld (SBSAV+2),a
  ld d,0
  pop bc
  pop hl
  ret
@@SPLIT@@
sb_s:
  ld a,d
  add a,a
  add a,d
  add a,a
  ld c,a
  ld b,0
  ld l,(hl)
  ld h,b
  add hl,hl
  add hl,bc
  call SG
sb_k:
  pop bc
  pop hl
  inc sp
  inc sp
  jp 7A14h
SBSAV: db 0,0,0
@@SPLIT@@
; 7A14h: tras dibujar, se devuelve la posicion original del cursor
SBREST:
  ld a,(SBSAV)
  or a
  jr z,sr_1
  xor a
  ld (SBSAV),a
  ld a,(SBSAV+1)
  ld (0060h),a
  ld a,(SBSAV+2)
  ld (0061h),a
sr_1:
  ld a,(0061h)
  ret
@@SPLIT@@
; tabla: fila, columna, cuantas, fila nueva (0 letra pequena, FFh nada), columna nueva (o x/2)
SBT:
  db 18,0,40,0FFh,0
  db 19,5,3,21,14
  db 19,32,3,21,23
  db 19,11,5,19,12
  db 19,24,5,19,23
  db 21,18,4,19,18
  db 21,5,11,0,18
  db 21,24,11,0,109
  db 22,19,2,21,19
  db 0
@@SPLIT@@
; letra pequena: E caracter, HL x en pixeles; lineas 168-174, tinta (73A4h) xor 1, fondo negro
SG:
  push hl
  ld a,e
  ld hl,{F2}
  cp 41h
  jr c,sg_1
  sub 41h-5
  jr sg_3
sg_1:
  cp 30h
  jr c,sg_2
  sub 30h
  ld hl,{F1}
  jr sg_3
sg_2:
  push hl
  ld hl,SGSP
  ld bc,4
  cpir
  pop hl
  ld a,0
  jr nz,sg_3
  ld a,4
  sub c
sg_3:
  jp SG2
SGSP: db 21h,2Ah,2Dh,2Eh
@@SPLIT@@
SG2:
  push hl
  ld l,a
  ld h,0
  ld d,h
  ld e,l
  add hl,hl
  add hl,hl
  add hl,hl
  or a
  sbc hl,de
  pop de
  add hl,de
  ld (sg_g+1),hl
  ld a,(73A4h)
  xor 1
  ld c,0
  rrca
  jr nc,sg_4
  ld c,0F0h
sg_4:
  rrca
  jr nc,sg_5
  ld a,c
  or 0Fh
  ld c,a
sg_5:
  jp SG3
@@SPLIT@@
SG3:
  ld a,c
  ld (sg_p+1),a
  pop hl
  ld a,l
  and 3
  ld b,a
  ld a,88h
  inc b
sg_6:
  dec b
  jr z,sg_7
  rrca
  jr sg_6
sg_7:
  ld (sg_m+1),a
  srl h
  rr l
  srl h
  rr l
  ld (sg_x+1),hl
  jp SG4
@@SPLIT@@
SG4:
  ld a,168
  ld b,7
sg_l:
  push bc
  push af
  call LADR
sg_x:
  ld hl,0
  add hl,de
  ld de,-8
  add hl,de
sg_g:
  ld de,0
  ld a,(de)
  inc de
  ld (sg_g+1),de
  ld e,a
sg_m:
  ld d,88h
  ld b,6
sg_px:
  sla e
sg_p:
  ld a,0
  jr c,sg_8
  ld a,0F0h
sg_8:
  xor (hl)
  and d
  xor (hl)
  ld (hl),a
  rrc d
  jr nc,sg_9
  inc hl
sg_9:
  djnz sg_px
  pop af
  inc a
  pop bc
  djnz sg_l
  ret
@@SPLIT@@
; menu (21EAh) y estadisticas de fin de periodo (1DE5h): fuera del partido
MENU2:
  call LEAVE
  jp {MENUH}
STAT2:
  xor a
  call TSET
  call LEAVE
  ld a,{C0}
  ld b,13
  call CLRL
  ld a,128
  ld b,18
  call CLRL
  jp 1E39h
@@SPLIT@@
; B lineas en negro desde la linea A (las 64 columnas del bufer)
CLRL:
  push bc
  call LADR
  ld h,d
  ld l,e
  inc de
  ld (hl),0F0h
  ld bc,63
  ldir
  pop bc
  inc a
  djnz CLRL
  ret
@@SPLIT@@
; borrado de pantalla (en lugar de 758Eh con HL=C000h, BC=4000h): las 25 filas de cada bloque, sin
; tocar sus zonas libres (desde +640h)
CLS:
  ld hl,0C000h
cl_1:
  ld a,(758Fh)
  ld (hl),a
  ld d,h
  ld e,l
  inc de
  ld bc,063Fh
  ldir
  ld bc,01C1h
  add hl,bc
  ld a,h
  or a
  jr nz,cl_1
  dec hl
  ld de,0
  ld b,d
  ld c,e
  ret
"""
# al arrancar (desde el bloque de A568h, que luego es el bufer): copia de datos a sus sitios fijos
INIT = """
MYINIT:
  di
  ld hl,BF1
  ld de,{F1}
  ld bc,70
  ldir
  ld hl,BF2
  ld de,{F2}
  ld bc,217
  ldir
  jp 0226h
"""
F1, F2 = 0x00E4, 0x0135       # letra pequena: cifras (10 x 7) y el resto (31 x 7) en memoria baja libre
INIT0 = 0xBB54                # bloque de arranque libre (ceros, sin uso hasta que A568h pasa a ser el bufer)


def apply(im):
    L0 = im.labels
    S = im.oldS
    N = design.build_static(S)
    C0 = design.CROWD0
    # el publico: las dos mitades iguales (la animacion usa la misma para las dos)
    N[C0:C0 + 31, 32 + 4 * 32:32 + 4 * 53] = N[C0:C0 + 31, 32 + 4 * 11:32 + 4 * 32]
    design.scoreboard(N)
    design.lcd(N, 152, 168, '30', design.PINK)
    # publico (lineas 11-41): bordes de la izquierda (columnas 9-10 del bufer; la derecha es su espejo)
    # y media fila (11-31); el resto en negro
    def mirb(v):
        r = 0
        for k in range(4):
            r |= ((v >> (7 - k)) & 1) << (4 + k) | ((v >> (3 - k)) & 1) << k
        return r
    top = bg.encode(N[C0:C0 + 31, 32:288])
    edges = bytearray(); crowd = bytearray(); xcrowd = bytearray()
    cheer = im.rd(CHEER, 21 * 2)
    for y in range(31):
        row = top[64 * y:64 * y + 64]
        edges += row[8:11]
        assert row[53:56] == bytes(mirb(v) for v in row[10:7:-1]), ('bordes', y)
        if y < 2: assert row[11:32] == cheer[21 * y:21 * y + 21]
        elif y < 17: crowd += row[11:32]
        else: xcrowd += row[11:32]
        for x in list(range(0, 8)) + list(range(56, 64)):
            if C0 + y >= 34 and x in (2, 3, 60, 61): continue     # tapas de los tableros (se dibujan aparte)
            assert row[x] == 0xF0, ('publico', y, x, hex(row[x]))
        assert row[32:53] == row[11:32]
    sb = b''.join(bg.encode(N[y:y + 1, 32:288]) for y in range(146, 184))
    sbz = lz.compress(sb)
    assert lz.decompress(sbz) == sb
    def dbs(name, data):
        out = [name + ':']
        for i in range(0, len(data), 16): out.append('  db ' + ','.join(str(b) for b in data[i:i + 16]))
        return '\n'.join(out) + '\n'
    data = ['@@SPLIT@@\n' + dbs('EDGES', edges), '@@SPLIT@@\n' + dbs('SBZ', sbz),
            '@@SPLIT@@\n' + dbs('XC1', crowd), '@@SPLIT@@\n' + dbs('XC2', xcrowd)]
    font = smallfont.data()
    fd = {c: font[7 * i:7 * i + 7] for i, c in enumerate(smallfont.ORDER)}
    f1 = b''.join(fd[c] for c in '0123456789')
    f2 = b''.join(fd[c] for c in ' !*-.ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    assert len(f2) == 217 and F2 + len(f2) <= 0x226 and F1 + len(f1) <= 0x12C
    mh = im.rd(0x21EA, 3); assert mh[0] == 0xCD
    src = SRC.replace('{MENUH}', str(mh[1] | mh[2] << 8)).replace('{F1}', str(F1)).replace('{F2}', str(F2))
    src = src.replace('{MD}', str(scrmap.MENU_D)).replace('{XC1}', 'XC1').replace('{XC2}', 'XC2').replace('{C0}', str(C0)).replace('{P5}', str(P5)).replace('{P6}', str(P6)).replace('{CHEER}', str(CHEER))
    src = src.replace('{TAB5}', str(line_addr(16 + design.DY) + 10)).replace('{TAB6}', str(line_addr(16 + design.DY) + 68))
    src += ''.join(data)
    # memoria liberada: piezas del marcador antiguo y su tabla, y el dibujo 8686h
    im.free.append([0x2DB4, P5])
    im.free.append([0x31E2, 0x3287])
    im.free.append([0x8686, 0x86B7])
    L = im.place_many('layout', src.split('@@SPLIT@@'))
    # bloque de arranque: MYINIT y los datos que copia
    from asm import assemble
    isrc = INIT.replace('{F1}', str(F1)).replace('{F2}', str(F2)) + dbs('BF1', f1) + dbs('BF2', f2)
    code, IL, _ = assemble(isrc, INIT0, dict(im.labels))
    assert INIT0 + len(code) <= 0xBF68 and im.rd(INIT0, len(code)) == bytes(len(code))
    im.poke(INIT0, code)
    im.init_end = INIT0 + len(code)
    im.poke(0x01FE, [0xC3] + [IL['MYINIT'] & 255, IL['MYINIT'] >> 8], [0xC3, 0x26, 0x02])
    im.poke(0x21EA, [0xCD, L['MENU2'] & 255, L['MENU2'] >> 8], mh)
    im.poke(0x1DE5, [0xC3, L['STAT2'] & 255, L['STAT2'] >> 8], [0xC3, 0x39, 0x1E])
    for a in (0x0277, 0x757A, 0x21C0):
        im.poke(a, [0xCD, L['CLS'] & 255, L['CLS'] >> 8], [0xCD, 0x8E, 0x75])
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x0FFF, [0xCD] + w(L['SETUP']), [0xCD, 0x86, 0x86])
    im.poke(0x02D6, [0xCD] + w(L['CHPD']), [0xCD] + w(L0['PDUMP']))
    im.poke(0x2190, [0xCD] + w(L['CHREC2']), [0xCD] + w(L0['CHREC']))
    # energia: 24 unidades y dibujo en dos barras
    for a in (0x03CF, 0x0F3F, 0x0FBB): im.poke(a, [0x18], [0x17])
    im.poke(0x1BE1, [0x18], [0x17])
    im.poke(0x1C57, [0xC3] + w(L['EUNIT']), [0x16, 0x00, 0x5F])
    ei = """
  ld l,59h
  ld a,(1139h)
  call ei_1
  ld l,80h
  ld a,(1153h)
ei_1:
  or a
  ret z
  ld b,a
ei_2:
  push bc
  push hl
  ld a,b
  dec a
  ld c,0Eh
  call EUNIT
  pop hl
  pop bc
  djnz ei_2
  ret
"""
    code, _, _ = assemble(ei, 0x1C5F, dict(im.labels))
    assert len(code) <= 0x1C7F - 0x1C5F, len(code)
    im.poke(0x1C5F, code, [0x21, 0x59, 0xED])
    # balon de posesion
    im.poke(0x07E9, [0x16], [0x13])
    im.poke(0x07F7, [0x38], [0x3B])
    # salida de caracteres del marcador
    im.poke(0x79E2, [0xCD] + w(L['SBCHR']), [0x5F, 0x16, 0x00])
    im.poke(0x7A14, [0xCD] + w(L['SBREST']), [0x3A, 0x61, 0x00])
    # nombres de como mucho 9 letras (ITURRIAGA)
    im.poke(0x22EB, [9], [10])
    im.poke(0x2309, [9], [10])
