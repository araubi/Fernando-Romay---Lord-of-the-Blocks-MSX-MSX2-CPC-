"""VERSION MSX2 SCREEN 5 (G4, 16 colores por pixel).

Idea general
- Fuera del partido el juego sigue en SCREEN 2 (G2), pero con sus tablas en la VRAM alta
  (banco R14=7: patrones 1C000h, nombres 1D800h, colores 1E000h). Todas las escrituras del juego
  van ahi porque R14 vale siempre 7 (cada rutina nueva que lo cambia lo restaura).
- En el partido (92AAh, montaje de la pantalla) se pasa a G4. VRAM:
    pagina 0 / 1 (y 0-191 / 256-447): dos pantallas (doble bufer, se cambian en el VBLANK)
    pagina 2 (y 512-703): fondo limpio (grada, cartel, canastas, pista)
    lineas ocultas 192-255, 448-511, 704-767 y pagina 3 (768-895): atlas de piezas
    pagina 3 (896-1023) = banco 7: la pantalla G2 del juego (sigue recibiendo sus escrituras)
- Piezas (B01Ch): en lugar de componer en C298h se copia la pieza del atlas con LMMM+TIMP a la
  pagina oculta; al principio del fotograma se restauran desde el fondo (HMMM) los rectangulos
  dibujados en esa pagina dos fotogramas antes. B1FEh pide el cambio de pagina al VBLANK.
- Marcador (filas 15-23): se convierte de G2 (patron + color por linea) a G4 celda a celda,
  leyendo la pantalla G2 de la VRAM; una suma de control por celda evita reconvertir lo que no cambia.
- Repeticiones: de momento se vuelve a G2 (la ampliacion del juego) y al acabar 92AAh entra otra vez."""
import re
from asm import assemble
import s5_assets as SA

# ---------------------------------------------------------------------------------------------
# memoria
ORGA, LIMA = 0xE334, 0xE740        # bloque A (extension del fichero 1)
ORGB, LIMB = 0xDC18, 0xDE44        # bloque B (glifos 60h-7Fh de la fuente + extension)
ORGN, LIMN = 0x8000, 0x8231        # bloque N (lo copia el cargador de la ROM)
ORGE, LIME = 0xE740, 0xF280        # bloque E (desde la ROM al entrar en el partido; el menu lo restaura con CF36h)
SWAPPED = 0x8231
CK = 0x8300                        # 288 sumas de control del marcador
RECTS0, RECTS1 = 0x8420, 0x8450    # 12 rectangulos x 4 bytes por pagina
PBUF, CBUF, OBUF = 0x8480, 0x8488, 0x8490
QT = 0x84B0                        # 4 bytes (alineado: L = B0..B3)
NRECT = 12
BANKE = 4                          # banco de la ROM con el bloque E
ASSET_BANK = 5                     # bancos 5-8: VRAM inicial (fondo y atlas)

COMMON = f"""
SWAPPED  equ {SWAPPED}
CK       equ {CK}
RECTS0   equ {RECTS0}
RECTS1   equ {RECTS1}
PBUF     equ {PBUF}
CBUF     equ {CBUF}
OBUF     equ {OBUF}
QT       equ {QT}
NRECT    equ {NRECT}
"""

# ---------------------------------------------------------------------------------------------
SRCA = """
; ===================== variables (se cargan con el fichero 1) =====================
S5ON:    db 0
DRAWPG:  db 0
FLIPREQ: db 0
FSTATE:  db 0
SETUP:   db 0
NREC0:   db 0
NREC1:   db 0
FULL0:   db 0
FULL1:   db 0
LASTIDX: db 0
PSIDE:   db 0
ROMSLOT: db 0
SAVA8:   db 0
ROTC:    dw 0
CROW:    db 0
CCOL:    db 0
CMASK:   db 0
FRMIN:   db 5
LASTF:   db 0
VBCNT:   db 0
REPLAY:  db 0
BULK:    db 0
FRESH:   db 0
CMDB:    ds 15

; ---------- 9E6Fh: recordar el indice de la pieza ----------
IDXH:
  ld (LASTIDX),a
  add a,a
  ld l,a
  ld h,0
  ret

; ---------- B01Ch (call): pieza ----------
PIECEH:
  ld a,(S5ON)
  or a
  jr nz,ph_s5
  ld hl,(0D09Ah)
  ret
ph_s5:
  pop hl
  ld a,ixl
  ld (PSIDE),a
  call FBEGIN
  jp S5PIECE

; ---------- B1F2h (jp): copia del fondo al bufer ----------
COPYH:
  ld a,(S5ON)
  or a
  ret nz
  ld hl,0B498h
  jp 0B1F5h

; ---------- B1FEh (jp): volcado -> fin de fotograma ----------
UPLH:
  ld a,(S5ON)
  or a
  jr nz,up_s5
  ld hl,0C298h
  jp 0B201h
up_s5:
  call FBEGIN
  call VWAIT
  ; ritmo del MSX1: como minimo FRMIN fotogramas por vuelta del bucle
  ld a,i
  jp po,up_nt
  ld a,(FRMIN)
  ld b,a
  ld hl,LASTF
up_th:
  ld a,(VBCNT)
  sub (hl)
  cp b
  jr c,up_th
  ld a,(VBCNT)
  ld (hl),a
up_nt:
  ld a,(DRAWPG)
  inc a
  ld (FLIPREQ),a
  dec a
  xor 1
  ld (DRAWPG),a
  xor a
  ld (FSTATE),a
  jp SBROT

; ---------- D4A0h (call, dentro de la interrupcion): cambio de pagina ----------
VBLHE:
  call VBLH
  jp 0D4C4h
VBLH:
  ld hl,VBCNT
  inc (hl)
  ld a,(FLIPREQ)
  or a
  ret z
  dec a
  rrca
  rrca
  rrca
  or 1Fh
  out (99h),a
  ld a,82h
  out (99h),a
  xor a
  ld (FLIPREQ),a
  ret
VBLF:
  ld a,(FLIPREQ)
  or a
  ret z
  dec a
  rrca
  rrca
  rrca
  or 1Fh
  out (99h),a
  ld a,82h
  out (99h),a
  xor a
  ld (FLIPREQ),a
  ret

; ---------- principio de fotograma: esperar el cambio y restaurar la pagina oculta ----------
FBEGIN:
  ld a,(FSTATE)
  or a
  ret nz
  inc a
  ld (FSTATE),a
  ld a,i
  jp po,fb_now
fb_w:
  ld a,(FLIPREQ)
  or a
  jr nz,fb_w
  jr fb_rest
fb_now:
  call VBLF
fb_rest:
  ld a,(REPLAY)
  or a
  jp nz,RPBEGIN
  ld a,(DRAWPG)
  or a
  ld hl,RECTS0
  ld de,NREC0
  jr z,fb_1
  ld hl,RECTS1
  ld de,NREC1
fb_1:
  inc de
  inc de
  ld a,(de)
  dec de
  dec de
  or a
  jr nz,fb_full
  ld a,(de)
  or a
  ret z
  ld b,a
  xor a
  ld (de),a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,2
  ld (CMDB+3),a
  ld a,(DRAWPG)
  ld (CMDB+7),a
fb_l:
  ld a,(hl)
  ld (CMDB+0),a
  ld (CMDB+4),a
  inc hl
  ld a,(hl)
  add a,8
  ld (CMDB+2),a
  ld (CMDB+6),a
  inc hl
  ld a,(hl)
  ld (CMDB+8),a
  inc hl
  ld a,(hl)
  ld (CMDB+10),a
  inc hl
  push hl
  push bc
  ld a,0D0h
  call VCMD
  pop bc
  pop hl
  djnz fb_l
  ret
fb_full:
  xor a
  ld (de),a
  inc de
  inc de
  ld (de),a
  ld hl,FULLCMD
  ld de,CMDB
  ld bc,15
  ldir
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld a,0D0h
  jp VCMD
FULLCMD:
  dw 0,520,0,8,256,112
  db 0,0,0

; ---------- comandos del VDP ----------
; VCMD: A = codigo de comando; registros 32-45 en CMDB
VCMD:
  ld (CMDB+14),a
  di
  ld a,2
  out (99h),a
  ld a,8Fh
  out (99h),a
vc_w:
  in a,(99h)
  rra
  jr c,vc_w
  xor a
  out (99h),a
  ld a,8Fh
  out (99h),a
  ld a,32
  out (99h),a
  ld a,91h
  out (99h),a
  ld hl,CMDB
  ld bc,0F9Bh
  otir
  ei
  ret
VWAIT:
  di
  ld a,2
  out (99h),a
  ld a,8Fh
  out (99h),a
vw_w:
  in a,(99h)
  rra
  jr c,vw_w
  xor a
  out (99h),a
  ld a,8Fh
  out (99h),a
  ei
  ret

; ---------- dibujar una pieza (LASTIDX, PSIDE, D098h = y, D099h = x/2) ----------
S5PIECE:
  ld a,(LASTIDX)
  cp 3Eh
  jr nc,sp_sh
  ld c,a
  ld a,(PSIDE)
  cp 25h
  ld b,0
  jr nz,sp_1
  inc b
sp_1:
  ld a,(SWAPPED)
  or a
  jr z,sp_2
  ld a,b
  xor 1
  ld b,a
  ld hl,REMAP
  ld e,c
  ld d,0
  add hl,de
  ld c,(hl)
sp_2:
  ld a,b
  or a
  ld a,c
  jr z,sp_ent
  add a,62
  jr sp_ent
sp_sh:
  cp 4Ah
  ret nc
  add a,124-3Eh
sp_ent:
  ld l,a
  ld h,0
  ld d,h
  ld e,l
  add hl,hl
  add hl,hl
  add hl,hl
  or a
  sbc hl,de
  ld de,ATAB
  add hl,de
  push hl
  pop iy
  ld a,(iy+3)
  or a
  ret z
  ; X = 2x + dx (recorte a la derecha)
  ld a,(0D099h)
  add a,a
  ret c
  add a,(iy+5)
  ret c
  ld (CMDB+4),a
  ld e,a
  ld d,(iy+3)
  add a,d
  jr nc,sp_w
  jr z,sp_w
  xor a
  sub e
  ld d,a
sp_w:
  ld a,d
  ld (CMDB+8),a
  ; Y = y (con signo) + dy
  ld a,(0D098h)
  ld l,a
  rla
  sbc a,a
  ld h,a
  ld a,(iy+6)
  add a,l
  ld l,a
  jr nc,sp_y1
  inc h
sp_y1:
  ld c,(iy+4)
  ld e,(iy+1)
  ld d,(iy+2)
  bit 7,h
  jr z,sp_top
  ld a,l
  neg
  cp c
  ret nc
  ld b,a
  ld a,c
  sub b
  ld c,a
  ld a,e
  add a,b
  ld e,a
  jr nc,sp_y2
  inc d
sp_y2:
  ld hl,0
sp_top:
  ld a,h
  or a
  ret nz
  ld a,l
  cp 112
  ret nc
  add a,c
  cp 113
  jr c,sp_bot
  ld a,112
  sub l
  ld c,a
sp_bot:
  ld a,(iy+0)
  ld (CMDB+0),a
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,e
  ld (CMDB+2),a
  ld a,d
  ld (CMDB+3),a
  ld a,l
  add a,8
  ld (CMDB+6),a
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld a,c
  ld (CMDB+10),a
  ; rectangulo para restaurar: x0 par, y del bufer, ancho par, alto
  ld b,l
  ld a,(REPLAY)
  or a
  jp nz,RPPIECE
  call RECADD
sp_go:
  ld a,98h
  jp VCMD

; RECADD: rectangulo a restaurar (CMDB+4 = X, CMDB+8 = ancho, B = y del bufer, C = alto)
RECADD:
  ld a,(DRAWPG)
  or a
  ld hl,NREC0
  ld de,RECTS0
  jr z,ra_1
  ld hl,NREC1
  ld de,RECTS1
ra_1:
  ld a,(hl)
  cp NRECT
  jr c,ra_2
  inc hl
  inc hl
  ld (hl),1
  ret
ra_2:
  inc (hl)
  add a,a
  add a,a
  add a,e
  ld e,a
  jr nc,ra_3
  inc d
ra_3:
  ld a,(CMDB+4)
  and 0FEh
  ld (de),a
  inc de
  ld a,b
  ld (de),a
  inc de
  ld a,(CMDB+4)
  and 1
  inc a
  ld hl,CMDB+8
  add a,(hl)
  and 0FEh
  ld (de),a
  inc de
  ld a,c
  ld (de),a
  ret

; ---------- trampolines residentes hacia el bloque E ----------
ZOOMT:
  ld a,(REPLAY)
  or a
  jp nz,ZOOMH
  ld iy,0C398h
  jp 0A8F8h
WIPET:
  ld a,(S5ON)
  or a
  jp nz,WIPEH
  ld ix,0D0ACh
  jp 0A0C3h

; ---------- A521h (jp): grada animada (HL = fila de 8 lineas / columna de bytes en el bufer) ----------
CROWDH:
  ld a,(S5ON)
  or a
  jr nz,cw_s5
  ld de,0C298h
  jp 0A524h
cw_s5:
  ld a,(REPLAY)
  or a
  ret nz
  push hl
  call FBEGIN
  pop hl
  ld a,l
  add a,a
  add a,a
  add a,a
  ld (CMDB+4),a
  ld a,h
  add a,a
  add a,a
  add a,a
  ld b,a
  add a,8
  ld (CMDB+6),a
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld de,ATAB+137*7
  ld a,l
  cp 10h
  jr c,cw_1
  ld de,ATAB+138*7
cw_1:
  ld a,(de)
  ld (CMDB+0),a
  inc de
  ld a,(de)
  ld (CMDB+2),a
  inc de
  ld a,(de)
  ld (CMDB+3),a
  inc de
  ld a,(de)
  ld (CMDB+8),a
  inc de
  ld a,(de)
  ld c,a
  ld (CMDB+10),a
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  call RECADD
  ld a,0D0h
  jp VCMD
"""

# ---------------------------------------------------------------------------------------------
SRCB = """
; ===================== marcador: G2 (pantalla del juego) -> G4 =====================
; RDCELL: CROW/CCOL -> PBUF, CBUF ; A = suma (nunca 0)
RDCELL:
  ld a,(CCOL)
  add a,a
  add a,a
  add a,a
  ld e,a
  ld a,(CROW)
  ld d,a
  ld c,0
  ld hl,PBUF
  di
  ld a,e
  out (99h),a
  ld a,d
  out (99h),a
  call RD8
  ld a,e
  out (99h),a
  ld a,d
  add a,20h
  out (99h),a
  call RD8
  ei
  ld a,c
  or 1
  ret
RD8:
  ld b,8
rd_l:
  in a,(98h)
  ld (hl),a
  inc hl
  add a,c
  rlca
  ld c,a
  djnz rd_l
  ret

; MKOBUF: PBUF/CBUF -> OBUF (32 bytes, 4 por linea)
MKOBUF:
  ld hl,PBUF
  ld de,OBUF
  ld b,8
mk_l:
  push bc
  push hl
  ld bc,8
  add hl,bc
  ld a,(hl)
  ld c,a
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  ld hl,LUT
  add a,l
  ld l,a
  ld a,(hl)
  ld b,a
  ld a,c
  and 0Fh
  ld hl,LUT
  add a,l
  ld l,a
  ld c,(hl)
  ld hl,QT
  ld a,c
  rlca
  rlca
  rlca
  rlca
  push af
  or c
  ld (hl),a
  inc l
  pop af
  or b
  ld (hl),a
  inc l
  ld a,b
  rlca
  rlca
  rlca
  rlca
  push af
  or c
  ld (hl),a
  inc l
  pop af
  or b
  ld (hl),a
  pop hl
  ld c,(hl)
  inc hl
  push hl
  ld h,QT/256
  ld b,4
mk_b:
  ld a,c
  rlca
  rlca
  ld c,a
  and 3
  or QT&255
  ld l,a
  ld a,(hl)
  ld (de),a
  inc de
  djnz mk_b
  pop hl
  pop bc
  djnz mk_l
  ret

; WRCELL: OBUF -> paginas indicadas en CMASK (bit 0, 1, 2) en la celda CROW/CCOL
WRCELL:
  ld c,0
wc_p:
  ld a,(CMASK)
  rrca
  ld (CMASK),a
  call c,WRPG
  inc c
  ld a,c
  cp 3
  jr c,wc_p
  di
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ei
  ret
WRPG:
  push bc
  ld a,(CROW)
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  ld b,a
  ld a,c
  add a,a
  add a,b
  di
  out (99h),a
  ld a,8Eh
  out (99h),a
  ei
  ld a,(CROW)
  and 0Fh
  add a,a
  add a,a
  or 40h
  ld d,a
  ld a,(CCOL)
  add a,a
  add a,a
  ld e,a
  ld hl,OBUF
  ld b,8
wp_l:
  di
  ld a,e
  out (99h),a
  ld a,d
  out (99h),a
  ei
  ld a,(hl)
  out (98h),a
  inc hl
  nop
  ld a,(hl)
  out (98h),a
  inc hl
  nop
  ld a,(hl)
  out (98h),a
  inc hl
  nop
  ld a,(hl)
  out (98h),a
  inc hl
  ld a,e
  add a,128
  ld e,a
  jr nc,wp_n
  inc d
wp_n:
  djnz wp_l
  pop bc
  ret

; CHKCELL: celda CROW/CCOL; si es del marcador solo se convierte si cambio
CHKCELL:
  push ix
  call RDCELL
  ld c,a
  ld a,(CROW)
  sub 15
  jr c,ck_play
  ld l,a
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,(CCOL)
  add a,l
  ld l,a
  ld de,CK
  add hl,de
  ld a,(hl)
  cp c
  jr z,ck_e
  ld (hl),c
ck_play:
  call MKOBUF
  ld a,(BULK)
  or a
  ld a,7
  jr z,ck_w
  ld a,1
ck_w:
  ld (CMASK),a
  call WRCELL
ck_e:
  pop ix
  ret

; SBROT: 4 celdas del marcador por fotograma (red de seguridad)
SBROT:
  ld b,4
sr_l:
  push bc
  ld hl,(ROTC)
  inc hl
  ld a,h
  cp 1
  jr c,sr_1
  ld a,l
  cp 32
  jr c,sr_1
  ld hl,0
sr_1:
  ld (ROTC),hl
  call CELLHL
  call CHKCELL
  pop bc
  djnz sr_l
  ret
; HL = indice 0..287 -> CROW/CCOL
CELLHL:
  ld a,l
  and 1Fh
  ld (CCOL),a
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,h
  add a,15
  ld (CROW),a
  ret
; SBFULL: todo el marcador
SBFULL:
  ld hl,0
sf_l:
  push hl
  call CELLHL
  call CHKCELL
  pop hl
  inc hl
  ld a,h
  or a
  jr z,sf_l
  ld a,l
  cp 32
  jr c,sf_l
  ret

; CVOK: Z si se puede convertir ya (G4, fuera del montaje y de la repeticion)
CVOK:
  ld a,(S5ON)
  dec a
  ret nz
  ld a,(SETUP)
  or a
  ret nz
  ld a,(REPLAY)
  or a
  ret

; ---------- D930h (call): caracter impreso ----------
PRCH:
  call 0D8C1h
  call CVOK
  ret nz
  ld a,(4102h)
  ld (CROW),a
  ld a,(4103h)
  ld (CCOL),a
  jp CHKCELL

; ---------- 9F48h (jp): barras de energia ----------
BARH:
  push hl
  call BARO
  pop hl
  call CVOK
  ret nz
  push af
  push bc
  push de
  push hl
  ld a,h
  ld (CROW),a
  ld a,l
  ld (CCOL),a
  call CHKCELL
  pop hl
  pop de
  pop bc
  pop af
  ret
BARO:
  push hl
  di
  ld a,l
  jp 9F4Bh
"""

# ---------------------------------------------------------------------------------------------
SRCN = """
; ---------- D252h (jp): imagen/colores de un rectangulo de celdas ----------
D252H:
  ld a,(S5ON)
  or a
  jr nz,dh_1
  ld hl,007Eh
  jp 0D255h
dh_1:
  ld a,(REPLAY)
  or a
  ret nz
  ld hl,007Eh
  call 0D255h
  ld a,(SETUP)
  or a
  ret nz
  ld a,(0D098h)
  rrca
  rrca
  rrca
  and 1Fh
  ld d,a
  ld a,(0D0A0h)
  rrca
  rrca
  rrca
  and 1Fh
  ret z
  ld b,a
  ld a,(0D099h)
  ld e,a
  ld a,(0D0A2h)
  or a
  ret z
  ld c,a
dh_r:
  ld a,d
  cp 24
  ret nc
  cp 15
  jr c,dh_n
  push bc
  push de
dh_c:
  ld a,d
  ld (CROW),a
  ld a,e
  ld (CCOL),a
  push bc
  push de
  call CHKCELL
  pop de
  pop bc
  inc e
  ld a,e
  cp 32
  jr nc,dh_x
  dec c
  jr nz,dh_c
dh_x:
  pop de
  pop bc
dh_n:
  inc d
  djnz dh_r
  ret

; ---------- 92AAh (jp): montaje de la pantalla del partido ----------
SETUPH:
  call S5ENTER
  ld a,(REPLAY)
  or a
  call nz,RPEND
  ld a,1
  ld (SETUP),a
  ld a,11h
  ld (0D1BCh),a
  call 92AFh
  xor a
  ld (SETUP),a
  ld a,(FRESH)
  or a
  jp z,SBFULL
  ld (BULK),a
  call SBFULL
  xor a
  ld (BULK),a
  ld (FRESH),a
  ; marcador de la pagina 0 -> paginas 1 y 2
  ld hl,SBCPY
  ld de,CMDB
  ld bc,15
  ldir
  ld a,0D0h
  call VCMD
  ld a,2
  ld (CMDB+7),a
  ld a,0D0h
  jp VCMD
SBCPY:
  dw 0,120,0,376,256,72
  db 0,0,0

; ---------- D4CAh (call D501h dentro de CLS) ----------
CLSH:
  ld a,(SETUP)
  or a
  jr nz,cl_m
  call S5EXIT
  jp 0D501h
cl_m:
  ld a,(S5ON)
  or a
  ret nz
  jp 0D501h

; ---------- A82Ch (call D501h): repeticion -> de momento en G2 ----------
RPLH:
  ld a,(S5ON)
  or a
  jp z,0D501h
  call RPSTART
  jp 0D501h

; ---------- entrada al menu (charsel MENUH) ----------
MENUX:
  call S5EXIT
  jp 0CF36h

; ---------- entrar / salir de G4 ----------
S5ENTER:
  ld a,(S5ON)
  or a
  ret nz
  ld a,(0FFE8h)
  and 2
  ld a,6
  jr z,se_n
  dec a
se_n:
  ld (FRMIN),a
  call 0D501h
  call LOADE
  ld hl,PALS5
  call SETPAL
  di
  ld a,06h
  out (99h),a
  ld a,80h
  out (99h),a
  ld a,1Fh
  out (99h),a
  ld a,82h
  out (99h),a
  ei
  ; marcador de la pagina 2 en negro (alli se guarda una copia del marcador convertido)
  ld hl,SBCLR
  ld de,CMDB
  ld bc,15
  ldir
  ld a,0C0h
  call VCMD
  ; paginas 0 y 1 <- fondo
  ld hl,ENTCMD
  ld de,CMDB
  ld bc,15
  ldir
  ld a,0D0h
  call VCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  call VCMD
  call VWAIT
  xor a
  ld (FLIPREQ),a
  ld (FSTATE),a
  ld (NREC0),a
  ld (NREC1),a
  ld (FULL0),a
  ld (FULL1),a
  ld hl,CK
  ld de,CK+1
  ld bc,287
  ld (hl),0EFh
  ldir
  inc a
  ld (DRAWPG),a
  ld (S5ON),a
  ld (FRESH),a
  jp 0D4F0h
ENTCMD:
  dw 0,512,0,0,256,192
  db 0,0,0
SBCLR:
  dw 0,0,0,632,256,72
  db 11h,0,0

S5EXIT:
  ld a,(S5ON)
  or a
  ret z
  call VWAIT
  xor a
  ld (S5ON),a
  ld (FLIPREQ),a
  di
  ld a,02h
  out (99h),a
  ld a,80h
  out (99h),a
  ld a,76h
  out (99h),a
  ld a,82h
  out (99h),a
  ei
  ld hl,PALDEF
  jp SETPAL

; HL -> 32 bytes de paleta
SETPAL:
  di
  xor a
  out (99h),a
  ld a,90h
  out (99h),a
  ld bc,209Ah
  otir
  ei
  ret

; ---------- bloque E desde la ROM ----------
LOADE:
  call ROMON
  ld a,{BANKE}
  ld (6000h),a
  ld hl,4000h
  ld de,{ORGE}
  ld bc,{LENE}
  ldir
  jp ROMOFF
ROMON:
  di
  in a,(0A8h)
  ld (SAVA8),a
  ld a,(ROMSLOT)
  bit 7,a
  jr nz,ro_b
  and 3
  rlca
  rlca
  ld h,a
  ld a,(SAVA8)
  and 0F3h
  or h
  out (0A8h),a
  ret
ro_b:
  ld h,40h
  jp 0024h
ROMOFF:
  ld a,(ROMSLOT)
  bit 7,a
  jr nz,rf_b
  ld a,(SAVA8)
  out (0A8h),a
  ei
  ret
rf_b:
  ld a,(0D222h)
  ld h,40h
  call 0024h
  ei
  ret
"""


def pal_bytes(pal):
    out = bytearray()
    for i in range(16):
        r, g, b = pal[i]; out += bytes([(r << 4) | b, g])
    return bytes(out)


def table_src():
    """tablas del bloque E (atlas) + LUT/paletas (residentes)"""
    pass


def names(src):
    return set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', src, re.M))


_cache = {}


def blockE_data(P):
    """ATAB: 124 entradas de jugador (personaje*62 + fotograma) + 12 comunes + insignia + 2 gradas, 7 bytes; REMAP 62"""
    from court import court_bits
    f3 = P.F['f3'][3]
    bits = court_bits(f3)
    bg = SA.background(bits)
    cl, cr = SA.cheer_images(f3, bits, bg)
    canvas, tab = SA.atlas_vram(P, {('*', 'cheerL'): cl, ('*', 'cheerR'): cr})
    PAIRS = {0x0A: 0x0B, 0x16: 0x17, 0x22: 0x23, 0x2E: 0x2F, 0x30: 0x33, 0x31: 0x34, 0x32: 0x35,
             0x36: 0x3A, 0x37: 0x3B, 0x38: 0x3C, 0x39: 0x3D}
    PAIRS.update({v: k for k, v in list(PAIRS.items())})
    ent = bytearray()
    def e(k):
        x, y, w, h, dx, dy = tab[k]
        return bytes([x, y & 255, y >> 8, w, h, dx, dy])
    for ci, ch in enumerate(('itu', 'romay')):
        other = 'romay' if ch == 'itu' else 'itu'
        for i in range(62):
            k = (ch, i) if (ch, i) in tab else (other, i)
            ent += e(k)
    for i in range(0x3E, 0x4A):
        ent += e(('*', i))
    ent += e(('*', 'badge'))
    ent += e(('*', 'cheerL'))
    ent += e(('*', 'cheerR'))
    remap = bytes(PAIRS.get(i, i) for i in range(62))
    return canvas, bytes(ent), remap


def build(P):
    """-> dict con los bloques ensamblados y etiquetas"""
    canvas, ent, remap = blockE_data(P)
    lut = SA.g2lut()
    pals5 = pal_bytes(SA.PAL)
    paldef = pal_bytes({i: c for i, c in enumerate(SA.DEF)})
    srcE = "ATAB:\n" + ''.join('  db ' + ','.join(str(b) for b in ent[i:i + 16]) + '\n' for i in range(0, len(ent), 16))
    srcE += "REMAP:\n" + ''.join('  db ' + ','.join(str(b) for b in remap[i:i + 16]) + '\n' for i in range(0, len(remap), 16))
    srcE += SRCE
    # tablas alineadas al final: HI, LO (x2 horizontal) y LBUF
    pre, _, _ = assemble(COMMON + srcE, ORGE, {n: 0 for n in names(SRCA) | names(SRCB) | names(SRCN)} | {'HI': 0, 'LBUF': 0, 'LUT': 0, 'PALS5': 0, 'PALDEF': 0})
    end = ORGE + len(pre)
    hi = (end + 255) & ~255
    srcE += '  ds %d\nHI:\n' % (hi - end)
    srcE += ''.join('  db ' + ','.join(str((b & 0xF0) | (b >> 4)) for b in range(k, k + 16)) + '\n' for k in range(0, 256, 16))
    srcE += ''.join('  db ' + ','.join(str(((b & 15) << 4) | (b & 15)) for b in range(k, k + 16)) + '\n' for k in range(0, 256, 16))
    srcE += 'LBUF:\n  ds 64\n'
    lenE = hi + 512 + 64 - ORGE
    srcN = SRCN.replace('{BANKE}', str(BANKE)).replace('{ORGE}', str(ORGE)).replace('{LENE}', str(lenE))
    srcA = SRCA + "PALS5:\n  db " + ','.join(str(b) for b in pals5) + "\n"
    srcA += "PALDEF:\n  db " + ','.join(str(b) for b in paldef) + "\n"
    srcB = SRCB
    # LUT alineada (16 bytes sin cruzar pagina): al final del bloque B se ajusta con ds
    blocks = [('A', srcA, ORGA, LIMA), ('B', srcB, ORGB, LIMB), ('N', srcN, ORGN, LIMN), ('E', srcE, ORGE, LIME)]
    # LUT en el bloque N: se coloca al principio alineada
    lutsrc = "LUT:\n  db " + ','.join(str(b) for b in lut) + "\n"
    blocks[2] = ('N', lutsrc + srcN, ORGN, LIMN)
    nm = {k: names(s) for k, s, _, _ in blocks}
    labs = {k: {n: 0 for n in nm[k]} for k, _, _, _ in blocks}
    for _ in range(8):
        out = {}; new = {}
        for k, src, org, lim in blocks:
            consts = {}
            for j, l in labs.items():
                if j != k: consts.update(l)
            code, L, a = assemble(COMMON + src, org, consts)
            out[k] = code; new[k] = {n: v for n, v in L.items() if n in nm[k]}
        if new == labs: break
        labs = new
    for k, src, org, lim in blocks:
        assert org + len(out[k]) <= lim, ('bloque lleno', k, hex(org + len(out[k])), hex(lim))
    L = {}
    for l in labs.values(): L.update(l)
    assert (L['LUT'] & 0xFF) <= 0xF0
    assert len(out['E']) == lenE
    return out, L, canvas


def patch(F, base, at, old, new):
    i = at - base
    assert bytes(F[i:i + len(old)]) == bytes(old), (hex(at), bytes(F[i:i + len(old)]).hex())
    F[i:i + len(new)] = bytes(new)


CUR = {}


def apply(F1, F2, F3):
    out, L, canvas = CUR['build']
    w = lambda v: [v & 255, v >> 8]
    p3 = lambda at, old, new: patch(F3, 0x84D0, at, old, new)
    p1 = lambda at, old, new: patch(F1, 0xB3B0, at, old, new)
    p3(0x9E6F, [0x87, 0x6F, 0x26, 0x00], [0xCD] + w(L['IDXH']) + [0x00])
    p3(0xB01C, [0x2A, 0x9A, 0xD0], [0xCD] + w(L['PIECEH']))
    p3(0xB1F2, [0x21, 0x98, 0xB4], [0xC3] + w(L['COPYH']))
    p3(0xB1FE, [0x21, 0x98, 0xC2], [0xC3] + w(L['UPLH']))
    p3(0x92AA, [0x3E, 0x11, 0x32, 0xBC, 0xD1], [0xC3] + w(L['SETUPH']) + [0, 0])
    p3(0x9F48, [0xE5, 0xF3, 0x7D], [0xC3] + w(L['BARH']))
    p3(0xA82C, [0xCD, 0x01, 0xD5], [0xCD] + w(L['RPLH']))
    p3(0xA8F4, [0xFD, 0x21, 0x98, 0xC3], [0xC3] + w(L['ZOOMT']) + [0])
    p3(0xA521, [0x11, 0x98, 0xC2], [0xC3] + w(L['CROWDH']))
    p3(0xA0BF, [0xDD, 0x21, 0xAC, 0xD0], [0xC3] + w(L['WIPET']) + [0])
    p1(0xD4A0, [0xCD, 0xC4, 0xD4], [0xCD] + w(L['VBLHE']))
    p1(0xD4CA, [0xCD, 0x01, 0xD5], [0xCD] + w(L['CLSH']))
    p1(0xD930, [0xCD, 0xC1, 0xD8], [0xCD] + w(L['PRCH']))
    p1(0xD252, [0x21, 0x7E, 0x00], [0xC3] + w(L['D252H']))
    # registros del VDP que carga LIB_INIT: G2 con las tablas en el banco 7
    p1(0xD1C4, [0x02, 0xE0, 0x06, 0xFF, 0x03, 0x36, 0x07, 0x04], [0x02, 0xE0, 0x76, 0xFF, 0x3B, 0x36, 0x07, 0x04])
    # bloque B: la parte que cae dentro del fichero 1 (DC18h-DD18h)
    cb = out['B']
    head = cb[:0xDD19 - ORGB]
    o = ORGB - 0xB3B0; F1[o:o + len(head)] = head


def ext():
    """bytes que se anaden al final del fichero 1 (DD19h .. E73Fh)"""
    out, L, canvas = CUR['build']
    ca, cb = out['A'], out['B']
    o = bytearray(LIMA - 0xDD19)
    o[ORGA - 0xDD19:ORGA - 0xDD19 + len(ca)] = ca
    tail = cb[0xDD19 - ORGB:]
    o[0:len(tail)] = tail
    return o


# ---------------------------------------------------------------------------------------------
# repeticion ampliada (bloque E): se dibuja a tamano real en la zona R (VRAM 1C000h, y 896-991,
# 128x96 = la zona que amplia el juego) y se amplia x2 con la CPU solo donde hubo cambios
SRCE = """
RFIRST:  db 0
RPXP:    db 0
RFMIN:   db 8
RPN:     db 0
RPREC:   ds 40
ZN0:     db 0
ZREC0:   ds 40
ZN1:     db 0
ZREC1:   ds 40
ZN:      db 0
ZX:      db 0
ZXO:     db 0
WDIR:    db 0

; ---------- A0BFh (jp): cortinilla entre jugadas ----------
; la jugada nueva ya esta dibujada en la pagina oculta: se descubre por columnas de 8 px
; con una banda negra delante, como el original (49 pasos, uno por fotograma)
WIPEH:
  call FBEGIN
  call VWAIT
  ld a,(0D0ACh)
  and 80h
  ld (WDIR),a
  ld c,31h
wp_l:
  push bc
  ld a,c
  sub 12h
  jr c,wp_d
  cp 32
  jr nc,wp_d
  call WCOLX
  ld (CMDB+4),a
  ld a,11h
  ld (CMDB+12),a
  ld a,0C0h
  call WCMD
wp_d:
  pop bc
  push bc
  ld a,c
  cp 21h
  jr nc,wp_h
  dec a
  call WCOLX
  ld (CMDB+0),a
  ld (CMDB+4),a
  ld a,(DRAWPG)
  ld (CMDB+3),a
  ld a,0D0h
  call WCMD
wp_h:
  halt
  pop bc
  dec c
  jr nz,wp_l
  ; la pagina visible tiene ahora lo mismo que la oculta: mismas listas de rectangulos
  ld a,(DRAWPG)
  or a
  ld hl,RECTS0
  ld de,RECTS1
  jr z,wp_c
  ex de,hl
wp_c:
  ld bc,48
  ldir
  ld a,(DRAWPG)
  or a
  ld hl,NREC0
  ld de,NREC1
  jr z,wp_c2
  ex de,hl
wp_c2:
  ld a,(hl)
  ld (de),a
  inc hl
  inc hl
  inc de
  inc de
  ld a,(hl)
  ld (de),a
  ret
; columna de 8 px (con espejo) -> x
WCOLX:
  ld b,a
  ld a,(WDIR)
  or a
  ld a,b
  jr z,wc_1
  ld a,31
  sub b
wc_1:
  add a,a
  add a,a
  add a,a
  ret
; comando sobre la columna: y 8-119 de la pagina visible (SY ya puesto si hace falta)
WCMD:
  push af
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,8
  ld (CMDB+2),a
  ld (CMDB+6),a
  ld (CMDB+8),a
  ld a,112
  ld (CMDB+10),a
  ld a,(DRAWPG)
  xor 1
  ld (CMDB+7),a
  pop af
  jp VCMD

RPSTART:
  ld a,1
  ld (REPLAY),a
  ld (RFIRST),a
  ld a,(FRMIN)
  add a,3
  ld (RFMIN),a
  xor a
  ld (RPN),a
  ld (ZN0),a
  ld (ZN1),a
  ld (NREC0),a
  ld (NREC1),a
  ld (FULL0),a
  ld (FULL1),a
  ret

RPEND:
  call 0D501h
  xor a
  ld (REPLAY),a
  ld (FSTATE),a
  ld (NREC0),a
  ld (NREC1),a
  ld (FULL0),a
  ld (FULL1),a
  ld hl,ENTCMD
  ld de,CMDB
  ld bc,15
  ldir
  ld a,0D0h
  call VCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  call VCMD
  jp VWAIT

; principio de fotograma en la repeticion
RPBEGIN:
  ld a,(RFIRST)
  dec a
  jr nz,rb_rest
  ld a,(0A8F9h)
  add a,a
  add a,a
  add a,a
  ld (RPXP),a
  ld a,2
  ld (RFIRST),a
  ld hl,RBCMD
  ld de,CMDB
  ld bc,15
  ldir
  ld a,(RPXP)
  ld (CMDB+0),a
  ld a,0D0h
  jp VCMD
RBCMD:
  dw 0,528,0,896,128,96
  db 0,0,0
rb_rest:
  ld a,(RPN)
  or a
  ret z
  ld b,a
  xor a
  ld (RPN),a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,2
  ld (CMDB+3),a
  ld a,3
  ld (CMDB+7),a
  ld hl,RPREC
rb_l:
  ld a,(RPXP)
  add a,(hl)
  ld (CMDB+0),a
  ld a,(hl)
  ld (CMDB+4),a
  inc hl
  ld a,(hl)
  add a,16
  ld (CMDB+2),a
  ld a,(hl)
  add a,80h
  ld (CMDB+6),a
  inc hl
  ld a,(hl)
  ld (CMDB+8),a
  inc hl
  ld a,(hl)
  ld (CMDB+10),a
  inc hl
  push hl
  push bc
  ld a,0D0h
  call VCMD
  pop bc
  pop hl
  djnz rb_l
  ret

; pieza en la repeticion: B = y del bufer, C = alto; CMDB: SX, SY, X (pantalla), NX
RPPIECE:
  ld a,b
  sub 8
  jr nc,rpp_y1
  neg
  cp c
  ret nc
  ld d,a
  ld a,c
  sub d
  ld c,a
  ld hl,(CMDB+2)
  ld e,d
  ld d,0
  add hl,de
  ld (CMDB+2),hl
  xor a
rpp_y1:
  cp 96
  ret nc
  ld b,a
  add a,c
  cp 97
  jr c,rpp_y2
  ld a,96
  sub b
  ld c,a
rpp_y2:
  ld a,(RPXP)
  ld e,a
  ld a,(CMDB+4)
  sub e
  jr nc,rpp_x1
  neg
  ld d,a
  ld a,(CMDB+8)
  sub d
  ret c
  ret z
  ld (CMDB+8),a
  ld a,(CMDB+0)
  add a,d
  ld (CMDB+0),a
  xor a
rpp_x1:
  cp 128
  ret nc
  ld (CMDB+4),a
  ld d,a
  ld a,(CMDB+8)
  add a,d
  cp 129
  jr c,rpp_x2
  ld a,128
  sub d
  ld (CMDB+8),a
rpp_x2:
  ld a,b
  add a,80h
  ld (CMDB+6),a
  ld a,3
  ld (CMDB+7),a
  ld a,c
  ld (CMDB+10),a
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,(RPN)
  cp 10
  jr nc,rpp_go
  inc a
  ld (RPN),a
  dec a
  add a,a
  add a,a
  ld e,a
  ld d,0
  ld hl,RPREC
  add hl,de
  ld a,(CMDB+4)
  and 0FEh
  ld (hl),a
  inc hl
  ld (hl),b
  inc hl
  ld a,(CMDB+4)
  and 1
  inc a
  ld e,a
  ld a,(CMDB+8)
  add a,e
  and 0FEh
  ld (hl),a
  inc hl
  ld (hl),c
rpp_go:
  ld a,98h
  jp VCMD

; insignia 'R' (parpadea como la del juego)
BADGE:
  ld hl,ATAB+136*7
  push hl
  pop iy
  ld a,(iy+0)
  ld (CMDB+0),a
  ld a,(iy+1)
  ld (CMDB+2),a
  ld a,(iy+2)
  ld (CMDB+3),a
  ld a,(iy+3)
  ld (CMDB+8),a
  ld c,(iy+4)
  ld a,(RPXP)
  or a
  ld a,24
  jr z,bd_1
  ld a,224
bd_1:
  ld (CMDB+4),a
  ld b,8
  jp RPPIECE

; ---------- A8F4h (jp): ampliacion ----------
ZOOMH:
  call FBEGIN
  ld a,(0D0CAh)
  or a
  call nz,BADGE
  call VWAIT
  ld a,(RFIRST)
  cp 2
  jr nz,zh_n
  ld a,3
  ld (RFIRST),a
  ld bc,0060h
  ld de,0080h
  call ZRECT
  ld hl,ZCPY
  ld de,CMDB
  ld bc,15
  ldir
  ld a,(DRAWPG)
  ld (CMDB+3),a
  xor 1
  ld (CMDB+7),a
  ld a,0D0h
  call VCMD
  ld hl,RPN
  ld de,ZN0
  ld bc,41
  ldir
  ld hl,RPN
  ld de,ZN1
  ld bc,41
  ldir
  jr zh_flip
zh_n:
  ld a,(DRAWPG)
  or a
  ld hl,ZN0
  jr z,zh_2
  ld hl,ZN1
zh_2:
  push hl
  call ZLIST
  ld hl,RPN
  call ZLIST
  pop de
  ld hl,RPN
  ld bc,41
  ldir
zh_flip:
  call VWAIT
  ld a,i
  jp po,zf_nt
  ld a,(RFMIN)
  ld b,a
  ld hl,LASTF
zf_th:
  ld a,(VBCNT)
  sub (hl)
  cp b
  jr c,zf_th
  ld a,(VBCNT)
  ld (hl),a
zf_nt:
  ld a,(DRAWPG)
  inc a
  ld (FLIPREQ),a
  dec a
  xor 1
  ld (DRAWPG),a
  xor a
  ld (FSTATE),a
  ret
ZCPY:
  dw 0,0,0,0,256,192
  db 0,0,0

ZLIST:
  ld a,(hl)
  or a
  ret z
  ld b,a
  inc hl
zl_l:
  push bc
  ld d,(hl)
  inc hl
  ld b,(hl)
  inc hl
  ld e,(hl)
  inc hl
  ld c,(hl)
  inc hl
  push hl
  call ZRECT
  pop hl
  pop bc
  djnz zl_l
  ret

; B = fila, C = filas, D = x0 (par), E = ancho (par) en la zona R -> pagina DRAWPG x2
ZRECT:
  ld a,e
  or a
  ret z
  rrca
  and 7Fh
  ld (ZN),a
  ld a,d
  ld (ZXO),a
  rrca
  and 7Fh
  ld (ZX),a
  ld a,c
  or a
  ret z
zr_row:
  push bc
  di
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,b
  rrca
  and 80h
  ld l,a
  ld a,(ZX)
  or l
  out (99h),a
  ld a,b
  rrca
  and 3Fh
  out (99h),a
  ei
  ld hl,LBUF
  ld a,(ZN)
  ld c,a
zr_r:
  in a,(98h)
  ld (hl),a
  inc l
  dec c
  jr nz,zr_r
  pop bc
  push bc
  ld a,(DRAWPG)
  add a,a
  ld l,a
  ld a,b
  rlca
  rlca
  and 3
  add a,l
  di
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,(ZXO)
  out (99h),a
  ld a,b
  and 3Fh
  or 40h
  out (99h),a
  ei
  call ZLINE
  pop bc
  push bc
  di
  ld a,(ZXO)
  or 80h
  out (99h),a
  ld a,b
  and 3Fh
  or 40h
  out (99h),a
  ei
  call ZLINE
  pop bc
  inc b
  dec c
  jr nz,zr_row
  di
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ei
  ret
ZLINE:
  ld de,LBUF
  ld a,(ZN)
  ld b,a
  ld h,HI/256
zl_b:
  ld a,(de)
  ld l,a
  ld a,(hl)
  out (98h),a
  inc h
  ld a,(hl)
  out (98h),a
  dec h
  inc e
  djnz zl_b
  ret
"""
