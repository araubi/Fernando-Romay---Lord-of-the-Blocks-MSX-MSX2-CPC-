"""Sin bufer de dibujo durante el partido: los jugadores, el balon y las redes se dibujan directamente
en pantalla. En cada vuelta se borran (fondo de 8B68h) solo los rectangulos donde se dibujo en la
anterior y se vuelven a dibujar. Asi se ahorran las dos copias de 6,5 KB por vuelta (fondo->bufer y
bufer->pantalla).
En la repeticion ampliada, el menu y el descanso se sigue usando el bufer de A568h como en el original
(la imagen ampliada se monta ahi).
- 84E8h: tabla de filas del dibujo de piezas: 8118h (pantalla) o 8278h (bufer).
- 84F5h: cada pieza dibujada en pantalla se apunta en la lista DLIST (fila, filas, x, ancho).
- 02D0h: antes de dibujar: se borran los rectangulos apuntados y se pinta el publico animado.
- 2199h: publico animado (solo durante el partido): directo a pantalla y se apunta.
- 835Ah: el volcado del bufer a pantalla no se hace en modo directo.
- 101Fh: al montar la pantalla del partido: fondo entero a pantalla y modo directo.
- 2417h (repeticion) y 7588h (fundido a negro): modo bufer."""
DLIST = 0x7354           # 12 entradas de 4 bytes + puntero (7354h-73A1h: ceros sin referencias)
DPTR = 0x7384
SRC = """
; el modo es la propia tabla del dibujo de piezas: (84E9h) = 81h directo (8118h), 82h bufer (8278h)
SETDIR:
  ld hl,8278h
  or a
  jr z,sd_1
  ld hl,8118h
sd_1:
  ld (84E8h),hl
  ret
@@SPLIT@@
; 84F5h: (85C6h) fila, (85C7h) filas, (85C8h) x, (85C9h) ancho
DREC:
  push de
  ld hl,85C7h
  ld a,(hl)
  or a
  jr z,dr_p
  ld b,a
  dec hl
  ld a,(hl)
  inc hl
  inc hl
  ld c,(hl)
  inc hl
  ld e,(hl)
  call DADD
  ld a,b
dr_p:
  pop de
  ret
@@SPLIT@@
; A fila, B filas, C x, E ancho
DADD:
  ld hl,(DPTR)
  ld (hl),a
  inc hl
  ld (hl),b
  inc hl
  ld (hl),c
  inc hl
  ld (hl),e
  inc hl
  jp DADD2
@@SPLIT@@
DADD2:
  ld a,l
  cp {DEND}
  ret z
  ld (DPTR),hl
  ret
@@SPLIT@@
; 02D0h: borrar lo dibujado en la vuelta anterior, publico animado y dibujar
EDRAW:
  call ERASE
  call 1DE8h
  jp 10A9h
@@SPLIT@@
ERASE:
  ld hl,{DLIST}
er_1:
  ld a,(DPTR)
  cp l
  jr z,er_end
  ld a,(hl)
  inc hl
  ld b,(hl)
  inc hl
  ld c,(hl)
  inc hl
  ld e,(hl)
  inc hl
  push hl
  jp er_2
er_end:
  ld hl,{DLIST}
  ld (DPTR),hl
  ret
@@SPLIT@@
er_2:
  push de
  ld l,a
  ld h,0
  add hl,hl
  push hl
  pop ix
  ld de,8118h
  add ix,de
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld d,0
  ld e,c
  add hl,de
  ld de,8B68h
  add hl,de
  pop de
  ld a,64
  call RECT
  pop hl
  jp er_1
@@SPLIT@@
; copia de un rectangulo a pantalla: HL origen, IX tabla de filas, B filas, C x, E ancho, A paso del origen
RECT:
  ld (RSTR+1),a
  ld a,c
  ld (RX+1),a
  ld a,e
  ld (RW+1),a
re_1:
  push bc
  ld e,(ix+0)
  ld d,(ix+1)
  inc ix
  inc ix
  ex de,hl
RX:
  ld bc,0
  add hl,bc
  ex de,hl
RW:
  ld bc,0
  push hl
  ldir
  pop hl
RSTR:
  ld c,0
  add hl,bc
  pop bc
  djnz re_1
  ret
@@SPLIT@@
; 2199h: publico animado (HL = columna 0Bh o 20h)
CHX:
  ld c,l
  xor a
  ld b,32
  ld e,21
  push bc
  call DADD
  pop bc
  ld e,21
  ld a,e
  ld hl,264Ah
  ld ix,8118h
  jp RECT
; 835Ah: sin volcado en modo directo
DGUARD:
  ld a,(84E9h)
  cp 82h
  ld hl,836Ah
  ret z
  pop hl
  ret
@@SPLIT@@
; 101Fh: pantalla del partido: fondo entero a pantalla, modo directo
FULLH:
  call MLOOP
  ld a,1
  call SETDIR
  call er_end
  ld hl,8B68h
  ld ix,8118h
  ld bc,6800h
  ld e,64
  ld a,e
  jp RECT
@@SPLIT@@
; final de MLOOP (bucle del partido): copia del fondo al bufer solo en modo bufer
MLB:
  ld a,(84E9h)
  cp 81h
  ret z
  jp 8348h
; 7588h (fundido a negro): modo bufer
BLK2:
  xor a
  call SETDIR
  jp BLACKH
@@SPLIT@@
; 2417h: repeticion (se monta en el bufer)
RPLH:
  xor a
  call SETDIR
  ld hl,6792h
  ret
"""
def apply(im):
    src = SRC.replace('{DLIST}', str(DLIST)).replace('{DEND}', str((DLIST + 48) & 255))
    im.labels['DPTR'] = DPTR
    im.free.append([DPTR + 2, 0x73A2])
    L = im.place_many('direct', src.split('@@SPLIT@@'))
    im.poke(DPTR, [DLIST & 255, DLIST >> 8], [0, 0])
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x84F5, [0xCD] + w(L['DREC']), [0x3A, 0xC7, 0x85])
    im.poke(0x02D0, [0xCD] + w(L['EDRAW']), [0xCD, 0xA9, 0x10])
    im.poke(0x02A6, [0, 0, 0], [0xCD, 0xE8, 0x1D])                 # el publico animado va en EDRAW
    im.poke(0x2199, [0xC3] + w(L['CHX']), [0x11, 0x68, 0xA5])
    im.poke(0x835A, [0xCD] + w(L['DGUARD']), [0x21, 0x6A, 0x83])
    im.poke(0x101F, [0xCD] + w(L['FULLH']), [0xCD] + w(im.labels['MLOOP']))
    im.poke(0x2417, [0xCD] + w(L['RPLH']), [0x21, 0x92, 0x67])
    a = im.labels['MLOOP']
    while im.rd(a, 3) != bytes([0xC3, 0x48, 0x83]): a += 1
    im.poke(a, [0xC3] + w(L['MLB']))
    im.poke(0x7588, [0xCD] + w(L['BLK2']), [0xCD] + w(im.labels['BLACKH']))
