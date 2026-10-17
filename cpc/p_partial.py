"""Volcado parcial en el partido (sin parpadeo y sin las dos copias completas de 6,5 KB por vuelta).
El juego sigue montando la imagen en el bufer de A568h, pero en cada vuelta:
- en el bufer solo se repone el fondo (8B68h) en los rectangulos donde se dibujo en la vuelta anterior;
- se dibujan las piezas en el bufer (cada una se apunta en la lista: fila, filas, x, ancho);
- a pantalla solo se copian los rectangulos de la vuelta anterior y de esta (lo que cambia).
El publico animado se apunta como un rectangulo (filas 0-31, x 0Bh-34h).
Si la lista se llena, o la imagen se ha montado por otro camino (inicio de periodo, repeticion,
fundido), en la vuelta siguiente se hace la copia y el volcado completos como el original.
Lista en 70D4h-7147h (29 entradas): es el final de la zona donde el arranque guardaba el area de
trabajo de AMSDOS (AC00h-B0FFh) para volver a BASIC, cosa que el juego nunca hace (ninguna tecla de la
tabla lleva a 74B9h); ese guardado (74ADh) se quita. El historial de la repeticion llega hasta 70D3h.
Punteros y bandera en 7390h-7394h; 7354h-738Fh queda para codigo."""
LIST = 0x70D4
PTR = 0x7390
MARK = 0x7392
FULLF = 0x7394
LEND = 0x7148
SRC = """
; 84F5h: (85C6h) fila, (85C7h) filas, (85C8h) x, (85C9h) ancho; devuelve A = filas
DREC:
  ld a,(85C7h)
  or a
  ret z
  push de
  ld b,a
  ld a,(85C6h)
  ld d,a
  jp DREC2
@@SPLIT@@
DREC2:
  ld hl,(85C8h)
  ld c,l
  ld e,h
  call DADD
  ld a,b
  pop de
  ret
@@SPLIT@@
; D fila, B filas, C x, E ancho
DADD:
  ld hl,(PTR)
  ld a,l
  cp {LEND}
  jp nz,DADD2
  ld a,2
  ld (FULLF),a
  ret
@@SPLIT@@
DADD2:
  ld (hl),d
  inc hl
  ld (hl),b
  inc hl
  ld (hl),c
  inc hl
  ld (hl),e
  inc hl
  ld (PTR),hl
  ret
@@SPLIT@@
; 2190h: publico animado (los dos rectangulos de una vez)
CHREC:
  ld d,0
  ld bc,200Bh
  ld e,42
  call DADD
  ld hl,000Bh
  ret
@@SPLIT@@
; final de MLOOP (02A3h y 101Fh): reponer el fondo en el bufer
PREST:
  ld hl,(PTR)
  ld (MARK),hl
  ld a,(FULLF)
  or a
  jp nz,8348h
  ld hl,8B68h
  ld de,8278h
  jp PCOPYL
@@SPLIT@@
; 02D6h: volcado de lo que cambia
PDUMP:
  ld hl,FULLF
  ld a,(hl)
  or a
  jr z,pd_1
  dec (hl)
  call 835Ah
  jr PSHIFT
pd_1:
  ld hl,0A568h
  ld de,8118h
  call PCOPYL
; las entradas nuevas (MARK..PTR) pasan a ser las de la vuelta anterior
PSHIFT:
  ld a,(PTR)
  ld hl,(MARK)
  sub l
  ld c,a
  ld b,0
  ld de,{LIST}
  jr z,ps_1
  ldir
ps_1:
  ld (PTR),de
  ret
@@SPLIT@@
; copia los rectangulos de la lista (LIST..PTR): origen HL (filas de 64 bytes), destino tabla de filas DE
; se usa la cadena de LDI del volcado original (8374h-83F7h), entrando segun el ancho
PCOPYL:
  ld (PCSRC+1),hl
  ld (PCTAB+2),de
  ld hl,PRL
  ld (83F5h),hl
  ld hl,{LIST}
Pcl_1:
  ld a,(PTR)
  cp l
  ret z
  ld d,(hl)
  inc hl
  ld b,(hl)
  inc hl
  ld c,(hl)
  inc hl
  ld e,(hl)
  inc hl
  push hl
  call PCOPY1
  pop hl
  jr Pcl_1
@@SPLIT@@
; un rectangulo: D fila, B filas, C x, E ancho
PCOPY1:
  ld a,c
  ld (PRX+1),a
  ld a,64
  sub e
  ld (PSK+1),a
  ld a,0F4h
  sub e
  sub e
  ld (PCH+1),a
  ld l,d
  ld h,0
  add hl,hl
  ex de,hl
PCTAB:
  ld ix,0
  add ix,de
  ld a,l
  ex de,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld e,c
  ld d,0
  add hl,de
PCSRC:
  ld de,0
  add hl,de
  push hl
  ld hl,0
  ld d,h
  ld e,a
Pcm_1:
  add hl,de
  djnz Pcm_1
  ld b,h
  ld c,l
  ld a,h
  or l
  pop hl
  ret z
  jp PRL0
@@SPLIT@@
; fin de cada fila de la cadena (jp pe): siguiente fila
PRL:
  ld a,l
PSK:
  add a,0
  ld l,a
  jr nc,PRL0
  inc h
PRL0:
  ld e,(ix+0)
  ld d,(ix+1)
  inc ix
  inc ix
  ld a,e
PRX:
  add a,0
  ld e,a
  jr nc,PCH
  inc d
PCH:
  jp 8374h
"""
def apply(im):
    src = SRC.replace('{LIST}', str(LIST)).replace('{LEND}', str(LEND & 255))
    im.labels.update({'PTR': PTR, 'MARK': MARK, 'FULLF': FULLF})
    im.poke(PTR, [LIST & 255, LIST >> 8, LIST & 255, LIST >> 8, 2], [0, 0, 0, 0, 0])
    im.free.append([FULLF + 1, 0x73A2])
    im.free.append([0x7354, 0x7390])
    im.poke(0x74AD, [0, 0, 0], [0xCD, 0xFE, 0x74])
    L = im.place_many('partial', src.split('@@SPLIT@@'))
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x84F5, [0xCD] + w(L['DREC']), [0x3A, 0xC7, 0x85])
    im.poke(0x2190, [0xCD] + w(L['CHREC']), [0x21, 0x0B, 0x00])
    im.poke(0x02D6, [0xCD] + w(L['PDUMP']), [0xCD, 0x5A, 0x83])
    a = im.labels['MLOOP']
    while im.rd(a, 3) != bytes([0xC3, 0x48, 0x83]): a += 1
    im.poke(a, [0xC3] + w(L['PREST']))
