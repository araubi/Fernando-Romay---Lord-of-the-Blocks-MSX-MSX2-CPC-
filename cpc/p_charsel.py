"""Eleccion de personaje en "1 JUGADOR" (JUGADOR 1: 1 - ITURRIAGA / 2 - F. ROMAY), como en MSX.
Si se elige a Romay se intercambian cabezas (tabla de piezas), saltos/tiros/mates (en espejo),
nombres y capacidades. Al volver al menu todo vuelve a su estado normal."""
JPAIRS = [(0x30, 0x33, 1), (0x31, 0x34, 1), (0x32, 0x35, 0), (0x36, 0x3A, 0), (0x37, 0x3B, 0),
          (0x38, 0x3C, 0), (0x39, 0x3D, 0)]
SRC = """
SWAPCH:
  ld hl,66F4h + 2*0Ah
  ld b,4
sw_h:
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld c,(hl)
  inc hl
  ld a,(hl)
  ld (hl),d
  dec hl
  ld (hl),e
  dec hl
  ld (hl),a
  dec hl
  ld (hl),c
  ld de,24
  add hl,de
  djnz sw_h
  ld hl,JTAB
  ld b,7
sw_j:
  push bc
  ld c,(hl)
  inc hl
  ld a,(hl)
  inc hl
  ld e,(hl)
  inc hl
  push hl
  ld hl,SHF
  ld (hl),e
  call MIRSW
  pop hl
  pop bc
  djnz sw_j
  ld hl,SPDCP+1
  ld a,(hl)
  xor 66h
  ld (hl),a
  ld hl,THRCP+1
  ld a,(hl)
  xor 66h
  ld (hl),a
  ld hl,DIJR
  ld a,(hl)
  xor 08h
  ld (hl),a
  ld hl,TOJR
  ld a,(hl)
  xor 08h
  ld (hl),a
  ld a,(SWAPPED)
  xor 1
  ld (SWAPPED),a
  ret
JTAB:
""" + '\n'.join('  db %d,%d,%d' % p for p in JPAIRS) + """
; C, A = indices: a <- espejo(b), b <- espejo(a)  (40 filas de 6 bytes; SHF = desplazamiento en bytes)
MIRSW:
  call SPADR
  push hl
  ld a,c
  call SPADR
  pop de
  ld b,40
ms_r:
  push bc
  push de
  push hl
  ld de,TMP
  ld bc,6
  ldir
  pop de
  pop hl
  push hl
  push de
  call MCPY
  pop hl
  pop de
  push hl
  push de
  ld hl,TMP
  call MCPY
  pop de
  pop hl
  ld bc,6
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  pop bc
  djnz ms_r
  ret
SPADR:
  add a,a
  ld l,a
  ld h,0
  ld de,66F4h
  add hl,de
  ld e,(hl)
  inc hl
  ld d,(hl)
  ld hl,32C8h + 2
  add hl,de
  ret
; DE <- espejo de la fila HL (6 bytes de modo 1), desplazada SHF bytes a la derecha
MCPY:
  push hl
  ld bc,5
  add hl,bc
  ld b,6
  ld a,(SHF)
  or a
  jr z,mc_l
  xor a
  ld (de),a
  inc de
  dec b
mc_l:
  ld a,(hl)
  push bc
  ld c,a
  ld b,8
mc_r:
  rr c
  rla
  djnz mc_r
  pop bc
  rlca
  rlca
  rlca
  rlca
  ld (de),a
  inc de
  dec hl
  djnz mc_l
  pop hl
  ret
; ---- 22A1h: tras elegir 1 o 2 jugadores ----
SELH:
  ld a,1
  ld (LCDON),a
  ld a,(110Eh)
  or a
  jr z,se_done
  ld hl,1638h
  ld (0064h),hl
  ld hl,0048h
  ld (006Ch),hl
  ld hl,0026h
  ld (006Eh),hl
  call 7424h
  ld de,SELTXT
  ld hl,0C08h
  call 10BBh
  ld hl,0C0Bh
  call 10BBh
  ld hl,0C0Dh
  call 10BBh
se_w0:
  call 233Ah
  ld a,(0063h)
  cp 0FFh
  jr nz,se_w0
se_w1:
  call 233Ah
  ld a,(0063h)
  cp 31h
  jr z,se_done
  cp 32h
  jr nz,se_w1
  call SWAPCH
  ld hl,1176h
  ld de,ITUNAME
  ld bc,11
  ldir
  ld hl,1182h
  ld de,1176h
  ld bc,11
  ldir
  ld hl,ITUNAME
  ld de,1182h
  ld bc,11
  ldir
  ld a,1
  ld (NSW),a
se_done:
  ld hl,0A80h
  ret
; ---- 21EAh: entrada al menu ----
MENUH:
  xor a
  ld (LCDON),a
  ld a,(SWAPPED)
  or a
  call nz,SWAPCH
  ld a,(NSW)
  or a
  jr z,mh_1
  xor a
  ld (NSW),a
  ld hl,ITUNAME
  ld de,1176h
  ld bc,11
  ldir
mh_1:
  ld a,0F0h
  ld (7469h),a
  ret
SELTXT:
  db 'JUGADOR 1',0FFh,'1 - ITURRIAGA',0FFh,'2 - F. ROMAY',0FFh
SHF: db 0
SWAPPED: db 0
NSW: db 0
TMP: ds 6
ITUNAME: ds 11
"""
def asm_str(src):
    import re
    return re.sub(r"'([^']*)'", lambda m: ','.join(str(ord(c)) for c in m.group(1)), src)
def apply(im):
    L = im.place('charsel', asm_str(SRC))
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x22A1, [0xCD] + w(L['SELH']), [0x21, 0x80, 0x0A])
    im.poke(0x21EA, [0xCD] + w(L['MENUH']) + [0, 0], [0x3E, 0xF0, 0x32, 0x69, 0x74])
