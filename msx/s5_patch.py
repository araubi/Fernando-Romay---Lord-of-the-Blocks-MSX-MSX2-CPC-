"""VERSION MSX2 SCREEN 5 (G4, 16 colores por pixel).

Idea general
- Fuera del partido el juego sigue en SCREEN 2 (G2), pero con sus tablas en la VRAM alta
  (banco R14=7: patrones 1C000h, nombres 1D800h, colores 1E000h). Todas las escrituras del juego
  van ahi porque R14 vale siempre 7 (cada rutina nueva que lo cambia lo restaura).
- En el partido (92AAh, montaje de la pantalla) se pasa a G4. VRAM (y de los comandos del VDP):
    pagina 0 / 1 (y 0-191 / 256-447): dos pantallas (doble bufer, se cambian en el VBLANK)
    pagina 2 (y 512-703): fondo limpio; y 632-703: copia del marcador ya convertido
    lineas ocultas 192-255, 448-511, 704-767 y pagina 3 (768-895): atlas de piezas
    pagina 3 (896-1023) = banco 7: la pantalla G2 del juego; en la repeticion, zona de dibujo
- Piezas (B01Ch): en lugar de componer en C298h se copia la pieza del atlas con LMMM+TIMP a la
  pagina oculta; al principio del fotograma se restauran desde el fondo (HMMM) los rectangulos
  dibujados en esa pagina dos fotogramas antes. B1FEh pide el cambio de pagina al VBLANK y
  mantiene el ritmo del MSX1 (5 fotogramas por vuelta en PAL, 6 en NTSC).
- Marcador (filas 15-23): se convierte de G2 (patron + color por linea) a G4 celda a celda,
  leyendo la pantalla G2 de la VRAM; una suma de control por celda evita reconvertir lo que no cambia.
- Repeticion: se dibuja a tamano real en la zona del banco 7 y se amplia x2 solo donde cambia.
- Codigo: residente en A (E334h), B (DC18h) y N (8000h); el resto (E, O1, O2) se carga desde la
  ROM al entrar en el partido: E en E740h (datos del menu, que los recupera con CF36h) y O1/O2 en
  zonas de codigo del menu (A53Ah, AC4Fh), que se restauran desde la ROM al salir."""
import re
from asm import assemble
import s5_assets as SA

# ---------------------------------------------------------------------------------------------
# memoria
ORGA, LIMA = 0xE334, 0xE740        # bloque A (extension del fichero 1)
ORGB, LIMB = 0xDC18, 0xDE44        # bloque B (glifos 60h-7Fh de la fuente + extension)
ORGN, LIMN = 0x8000, 0x8231        # bloque N (lo copia el cargador de la ROM)
ORGE, LIME = 0xE740, 0xF280        # bloque E (desde la ROM al entrar en el partido)
ORGO1, LIMO1 = 0xA53A, 0xA75F      # O1: codigo del menu (se restaura al salir)
ORGO2, LIMO2 = 0xAC4F, 0xAF05      # O2: codigo del menu de configuracion
SWAPPED = 0x8231
PBUF, CBUF, QT, LASTC, DIRTY = 0x8240, 0x8248, 0x8250, 0x8254, 0x8255
NT = 0x8300                        # 16 x 2 bytes (alineado)
CK = 0x8320                        # 288 sumas de control del marcador
RECTS0, RECTS1 = 0x8440, 0x8470    # 12 rectangulos x 4 bytes por pagina
NRECT = 12
BANKE = 4                          # banco de la ROM: E (0000h), O1 (1000h), O2 (1400h), originales (2000h, 2400h)
ROM_O1, ROM_O2, ROM_O1ORIG, ROM_O2ORIG, ROM_CK, ROM_MENU = 0x1000, 0x1400, 0x2000, 0x2400, 0x2800, 0x3000
BLANKCK = 0xEF                     # suma de control de una celda vacia (patron 0, color 11h)

COMMON = f"""
SWAPPED  equ {SWAPPED}
PBUF     equ {PBUF}
CBUF     equ {CBUF}
QT       equ {QT}
LASTC    equ {LASTC}
DIRTY    equ {DIRTY}
NT       equ {NT}
CK       equ {CK}
RECTS0   equ {RECTS0}
RECTS1   equ {RECTS1}
NRECT    equ {NRECT}
BANKE    equ {BANKE}
ORGE     equ {ORGE}
ORGO1    equ {ORGO1}
ORGO2    equ {ORGO2}
LENO1    equ {LIMO1 - ORGO1}
LENO2    equ {LIMO2 - ORGO2}
ROMO1    equ {0x4000 + ROM_O1}
ROMO2    equ {0x4000 + ROM_O2}
ROMO1OR  equ {0x4000 + ROM_O1ORIG}
ROMO2OR  equ {0x4000 + ROM_O2ORIG}
ROMCK    equ {0x4000 + ROM_CK}
ROMMENU  equ {0x4000 + ROM_MENU}
BLANKCK  equ {BLANKCK}
"""

# =============================================================================================
# A: residente (variables, piezas, fotograma, VDP)
SRCA = """
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
FRMIN:   db 5
LASTF:   db 0
VBCNT:   db 0
REPLAY:  db 0
BULK:    db 0
FRESH:   db 0
CKVALID: db 0
TXON:    db 0
TXR0:    db 0
TXR1:    db 0
TXC0:    db 0
TXC1:    db 0
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
  ld a,(FRMIN)
  call THROT
  ld a,(DRAWPG)
  inc a
  ld (FLIPREQ),a
  dec a
  xor 1
  ld (DRAWPG),a
  xor a
  ld (FSTATE),a
  ld a,(FRESH)
  or a
  jp z,SBROT
  xor a
  ld (FRESH),a
  jp SBFULL
; THROT: esperar hasta que hayan pasado A fotogramas desde la ultima vez
THROT:
  ld b,a
  ld a,i
  ret po
  ld hl,LASTF
th_l:
  ld a,(VBCNT)
  sub (hl)
  cp b
  jr c,th_l
  ld a,(VBCNT)
  ld (hl),a
  ret

; ---------- D4A0h (call, dentro de la interrupcion): contador y cambio de pagina ----------
VBLHE:
  ld hl,VBCNT
  inc (hl)
  call VBLF
  jp 0D4C4h
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
  ld a,(TXON)
  or a
  call nz,TXERASE
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
  call CMDLD
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld a,0D0h
  jp VCMD
FULLCMD:
  dw 0,520,0,8,256,112
  db 0,0,0
; TXERASE: caja de texto sobre la pista <- fondo, en las paginas 0 y 1
TXERASE:
  xor a
  ld (TXON),a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+7),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,2
  ld (CMDB+3),a
  ld a,(TXC0)
  add a,a
  add a,a
  add a,a
  ld (CMDB+0),a
  ld (CMDB+4),a
  ld b,a
  ld a,(TXC1)
  inc a
  add a,a
  add a,a
  add a,a
  sub b
  ld (CMDB+8),a
  ld a,(TXR0)
  add a,a
  add a,a
  add a,a
  ld (CMDB+2),a
  ld (CMDB+6),a
  ld b,a
  ld a,(TXR1)
  inc a
  add a,a
  add a,a
  add a,a
  sub b
  ld (CMDB+10),a
  ld a,0D0h
  call VCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  jp VCMD
; CMDLD: HL -> 15 bytes a CMDB
CMDLD:
  ld de,CMDB
  ld bc,15
  ldir
  ret

; ---------- comandos del VDP ----------
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
  ld b,l
  ld a,(REPLAY)
  or a
  jp nz,RPPIECE
  call RECADD
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

; ---------- trampolines residentes hacia los bloques cargables ----------
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
CROWDT:
  ld a,(S5ON)
  or a
  jp nz,CROWDH
  ld de,0C298h
  jp 0A524h
"""

# =============================================================================================
# B: residente (enganches del marcador y de la pantalla)
SRCB = """
; ---------- D930h (call): caracter impreso ----------
PRCH:
  call 0D8C1h
  ld a,(S5ON)
  or a
  ret z
  ld a,(REPLAY)
  or a
  ret nz
  ld a,(4102h)
  ld (CROW),a
  ld a,(4103h)
  ld (CCOL),a
  ld a,(SETUP)
  or a
  jp nz,MARKD
  jp CHKCELL

; ---------- 9F48h (jp): barras de energia ----------
BARH:
  push hl
  call BARO
  pop hl
  ld a,(S5ON)
  or a
  ret z
  push af
  push bc
  push de
  push hl
  ld a,h
  ld (CROW),a
  ld a,l
  ld (CCOL),a
  ld a,(REPLAY)
  or a
  jr nz,bh_e
  ld a,(SETUP)
  or a
  jr z,bh_c
  call MARKD
  jr bh_e
bh_c:
  call CHKCELL
bh_e:
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
  jp z,D252C
  ; en el montaje: el marco del marcador (AFFCh) y el color de la fila 15 (A778h) son fijos
  pop hl
  push hl
  ld de,0AFFCh
  or a
  sbc hl,de
  ret z
  pop hl
  push hl
  ld de,0A778h
  or a
  sbc hl,de
  ret z
  jp D252C

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
  jp SETEND

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

; ---------- A82Ch (call D501h): repeticion ----------
RPLH:
  ld a,(S5ON)
  or a
  jp z,0D501h
  call RPSTART
  jp 0D501h

; ---------- entrada al menu: charsel MENUH (call) y A0A1h (jp) ----------
MENUX:
  jp S5EXIT
MENUY:
  call S5EXIT
  jp 0A53Ah
; ---------- A1E1h (call A0BFh): pantalla de descanso / fin -> G2 con la cortinilla original ----------
RESTH:
  call S5EXIT
  jp 0A0BFh
; ---------- 8508h (ld hl,7EAFh): menu principal -> G2 y graficos del menu ----------
MENUZ:
  call S5EXIT
  ld hl,7EAFh
  ret
; ---------- 8538h (call 91B5h): vuelta al juego tras el descanso -> G4 ----------
RESUMH:
  call S5ENTER
  jp 91B5h
"""

# =============================================================================================
# N: residente (entrar/salir de G4, ROM, paletas)
SRCN = """
LUT:
  db {LUT}

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
  ld hl,ENTCMD
  call CMDLD
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
  ld (REPLAY),a
  ld hl,DIRTY
  ld de,DIRTY+1
  ld bc,35
  ld (hl),a
  ldir
  inc a
  ld (DRAWPG),a
  ld (S5ON),a
  ld (FRESH),a
  jp 0D4F0h
ENTCMD:
  dw 0,512,0,0,256,192
  db 0,0,0

S5EXIT:
  ld a,(S5ON)
  or a
  ret z
  call VWAIT
  xor a
  ld (S5ON),a
  ld (FLIPREQ),a
  ld (REPLAY),a
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
  call SETPAL
  ; codigo original del menu en O1 y O2
  call ROMON
  ld a,BANKE
  ld (6000h),a
  ld hl,ROMO1OR
  ld de,ORGO1
  ld bc,LENO1
  ldir
  ld hl,ROMO2OR
  ld de,ORGO2
  ld bc,LENO2
  ldir
  ld hl,ROMMENU
  ld de,ORGE
  ld bc,0B40h
  ldir
  jp ROMOFF

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

; ---------- bloques E, O1 y O2 desde la ROM ----------
LOADE:
  call ROMON
  ld a,BANKE
  ld (6000h),a
  ld hl,4000h
  ld de,ORGE
  ld bc,{LENE}
  ldir
  ld hl,ROMO1
  ld de,ORGO1
  ld bc,{LENO1C}
  ldir
  ld hl,ROMO2
  ld de,ORGO2
  ld bc,{LENO2C}
  ldir
  ; sumas de control del marcador precalculado (la primera vez)
  ld a,(CKVALID)
  or a
  jr nz,le_1
  inc a
  ld (CKVALID),a
  ld hl,ROMCK
  ld de,CK
  ld bc,288
  ldir
le_1:
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

# =============================================================================================
# O1: marcador (G2 -> G4)
SRCO1 = """
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
  ld b,8
rd_1:
  in a,(98h)
  ld (hl),a
  inc l
  add a,c
  rlca
  ld c,a
  djnz rd_1
  ld a,e
  out (99h),a
  ld a,d
  add a,20h
  out (99h),a
  ld b,8
rd_2:
  in a,(98h)
  ld (hl),a
  inc l
  add a,c
  rlca
  ld c,a
  djnz rd_2
  ei
  ld a,c
  or 1
  ret

; MKNT: color A -> NT (16 nibbles x 2 bytes) ; conserva HL, DE, BC
MKNT:
  ld (LASTC),a
  push hl
  push de
  push bc
  ld c,a
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  ld hl,LUT
  add a,l
  ld l,a
  ld d,(hl)
  ld a,c
  and 0Fh
  ld hl,LUT
  add a,l
  ld l,a
  ld e,(hl)
  ld hl,QT
  ld a,e
  rlca
  rlca
  rlca
  rlca
  ld c,a
  or e
  ld (hl),a
  inc l
  ld a,c
  or d
  ld (hl),a
  inc l
  ld a,d
  rlca
  rlca
  rlca
  rlca
  ld c,a
  or e
  ld (hl),a
  inc l
  ld a,c
  or d
  ld (hl),a
  ld hl,NT
  ld de,QT
  ld b,4
nt_o:
  ld a,(de)
  ld c,a
  push de
  ld de,QT
  ld (hl),c
  inc l
  ld a,(de)
  ld (hl),a
  inc l
  inc e
  ld (hl),c
  inc l
  ld a,(de)
  ld (hl),a
  inc l
  inc e
  ld (hl),c
  inc l
  ld a,(de)
  ld (hl),a
  inc l
  inc e
  ld (hl),c
  inc l
  ld a,(de)
  ld (hl),a
  inc l
  pop de
  inc e
  djnz nt_o
  pop bc
  pop de
  pop hl
  ret

; WRP: PBUF/CBUF -> celda CROW/CCOL de la pagina A (0..2)
WRP:
  ld b,a
  ld a,(CROW)
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  ld c,a
  ld a,b
  add a,a
  add a,c
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
  ld hl,PBUF
  ld b,8
wr_l:
  ld a,l
  add a,8
  ld l,a
  ld c,(hl)
  ld a,l
  sub 8
  ld l,a
  ld a,(LASTC)
  cp c
  ld a,c
  call nz,MKNT
  di
  ld a,e
  out (99h),a
  ld a,d
  out (99h),a
  ei
  push de
  ld d,NT/256
  ld a,(hl)
  and 0F0h
  rrca
  rrca
  rrca
  ld e,a
  ld a,(de)
  out (98h),a
  inc e
  nop
  ld a,(de)
  out (98h),a
  ld a,(hl)
  and 0Fh
  add a,a
  ld e,a
  ld a,(de)
  out (98h),a
  inc e
  nop
  ld a,(de)
  out (98h),a
  pop de
  inc l
  ld a,e
  add a,128
  ld e,a
  jr nc,wr_n
  inc d
wr_n:
  djnz wr_l
  di
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ei
  ret

; CHKCELL: celda CROW/CCOL; si es del marcador solo se convierte si cambio
CHKCELL:
  call RDCELL
  ld c,a
  ld a,(CROW)
  sub 15
  jr c,ck_go
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
  ret z
  ld (hl),c
  ld a,(BULK)
  or a
  jr z,ck_go
  xor a
  jp WRP
ck_go:
  ld a,(CROW)
  cp 15
  jp c,TXCELL
  ld a,2
  call WRP
; celda de la pagina 2 -> paginas 0 y 1
  ld a,(CCOL)
  add a,a
  add a,a
  add a,a
  ld (CMDB+0),a
  ld (CMDB+4),a
  ld a,(CROW)
  add a,a
  add a,a
  add a,a
  ld (CMDB+2),a
  ld (CMDB+6),a
  ld a,2
  ld (CMDB+3),a
  xor a
  ld (CMDB+7),a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,8
  ld (CMDB+8),a
  ld (CMDB+10),a
  ld a,0D0h
  call VCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  jp VCMD

; MARKD: celda CROW/CCOL pendiente (durante el montaje)
MARKD:
  ld a,(CROW)
  sub 15
  ret c
  cp 9
  ret nc
  add a,a
  add a,a
  ld e,a
  ld a,(CCOL)
  rrca
  rrca
  rrca
  and 3
  add a,e
  ld e,a
  ld d,0
  ld hl,DIRTY
  add hl,de
  ld a,(CCOL)
  and 7
  ld b,a
  ld a,1
  jr z,mk_2
mk_1:
  add a,a
  djnz mk_1
mk_2:
  or (hl)
  ld (hl),a
  ret

"""

# =============================================================================================
# O2: grada animada, cortinilla, fin del montaje, texto sobre la pista
SRCO2 = """
WDIR:    db 0
; TXCELL: texto sobre la pista: paginas 0 y 1 (no el fondo); se borra al empezar el siguiente fotograma
TXCELL:
  xor a
  call WRP
  ld a,(CCOL)
  add a,a
  add a,a
  add a,a
  ld (CMDB+0),a
  ld (CMDB+4),a
  ld a,(CROW)
  add a,a
  add a,a
  add a,a
  ld (CMDB+2),a
  ld (CMDB+6),a
  xor a
  ld (CMDB+1),a
  ld (CMDB+3),a
  ld (CMDB+5),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  inc a
  ld (CMDB+7),a
  ld a,8
  ld (CMDB+8),a
  ld (CMDB+10),a
  ld a,0D0h
  call VCMD
  ld hl,TXON
  ld a,(hl)
  or a
  ld a,(CROW)
  ld b,a
  ld a,(CCOL)
  ld c,a
  jr nz,tx_u
  ld (hl),1
  inc hl
  ld (hl),b
  inc hl
  ld (hl),b
  inc hl
  ld (hl),c
  inc hl
  ld (hl),c
  ret
tx_u:
  inc hl
  ld a,b
  cp (hl)
  jr nc,tx_1
  ld (hl),b
tx_1:
  inc hl
  cp (hl)
  jr c,tx_2
  ld (hl),b
tx_2:
  inc hl
  ld a,c
  cp (hl)
  jr nc,tx_3
  ld (hl),c
tx_3:
  inc hl
  cp (hl)
  ret c
  ld (hl),c
  ret

; D252C: rectangulo de D252h (marcar o convertir las celdas de las filas 15-23)
D252C:
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
dc_r:
  ld a,d
  cp 24
  ret nc
  cp 15
  jr c,dc_n
  push bc
  push de
dc_c:
  ld a,d
  ld (CROW),a
  ld a,e
  ld (CCOL),a
  push bc
  push de
  ld a,(SETUP)
  or a
  jr z,dc_k
  call MARKD
  jr dc_k2
dc_k:
  call CHKCELL
dc_k2:
  pop de
  pop bc
  inc e
  ld a,e
  cp 32
  jr nc,dc_x
  dec c
  jr nz,dc_c
dc_x:
  pop de
  pop bc
dc_n:
  inc d
  djnz dc_r
  ret

SETEND:
  xor a
  ld (FRESH),a
se_d:
  ld hl,DIRTY
  ld c,15
se_r:
  ld b,0
se_b:
  ld a,(hl)
  or a
  jr z,se_nb
  ld e,a
  ld d,8
  ld a,b
se_bit:
  srl e
  jr nc,se_nx
  push af
  push bc
  push de
  push hl
  ld (CCOL),a
  ld a,c
  ld (CROW),a
  call CHKCELL
  pop hl
  pop de
  pop bc
  pop af
se_nx:
  inc a
  dec d
  jr nz,se_bit
  ld (hl),0
se_nb:
  inc hl
  ld a,b
  add a,8
  ld b,a
  cp 32
  jr c,se_b
  inc c
  ld a,c
  cp 24
  jr c,se_r
  ret

; SBROT: 4 celdas del marcador por fotograma (red de seguridad)
SBROT:
  ld b,4
sr_l:
  push bc
  ld hl,(ROTC)
  inc hl
  ld a,h
  or a
  jr z,sr_1
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

; ---------- A521h: grada animada (HL = fila de 8 lineas / columna de bytes en el bufer) ----------
CROWDH:
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

; ---------- A0BFh: cortinilla entre jugadas ----------
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
"""

# =============================================================================================
# E: atlas + repeticion ampliada (zona R: VRAM 1C000h, y 896-991, 128x96)
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

; tras la repeticion: pantallas de nuevo con el fondo y el marcador (copia de la pagina 2)
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
  call CMDLD
  ld a,0D0h
  call VCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  call VCMD
  jp VWAIT

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
  call CMDLD
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

; ---------- A8F4h: ampliacion ----------
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
  call CMDLD
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
  ld a,(RFMIN)
  call THROT
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


def pal_bytes(pal):
    out = bytearray()
    for i in range(16):
        r, g, b = pal[i]; out += bytes([(r << 4) | b, g])
    return bytes(out)


def names(src):
    return set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', src, re.M))


def dbs(data, label=None):
    s = (label + ':\n') if label else ''
    return s + ''.join('  db ' + ','.join(str(b) for b in data[i:i + 16]) + '\n' for i in range(0, len(data), 16))


def blockE_data(P):
    """ATAB: 124 entradas de jugador (personaje*62 + fotograma) + 12 comunes + insignia + 2 gradas, 7 bytes; REMAP 62"""
    from court import court_bits
    f3 = P.F['f3'][3]
    bits = court_bits(f3)
    bg = SA.background(bits, P)
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
    return canvas, bytes(ent), remap, bg


def build(P):
    """-> (bloques ensamblados, etiquetas, atlas, fondo)"""
    canvas, ent, remap, bg = blockE_data(P)
    lut = SA.g2lut()
    srcA = SRCA + dbs(pal_bytes(SA.PAL), 'PALS5') + dbs(pal_bytes({i: c for i, c in enumerate(SA.DEF)}), 'PALDEF')
    srcE = dbs(ent, 'ATAB') + dbs(remap, 'REMAP') + SRCE
    # tablas alineadas al final de E: HI, LO (x2 horizontal) y LBUF
    allnames = names(srcA) | names(SRCB) | names(SRCN) | names(SRCO1) | names(SRCO2) | {'HI', 'LBUF', 'LUT'}
    pre, _, _ = assemble(COMMON + srcE, ORGE, {n: 0 for n in allnames})
    end = ORGE + len(pre)
    hi = (end + 255) & ~255
    srcE += '  ds %d\nHI:\n' % (hi - end)
    srcE += dbs(bytes((b & 0xF0) | (b >> 4) for b in range(256)))
    srcE += dbs(bytes(((b & 15) << 4) | (b & 15) for b in range(256)))
    srcE += 'LBUF:\n  ds 64\n'
    lenE = hi + 512 + 64 - ORGE
    srcN = SRCN.replace('{LUT}', ','.join(str(b) for b in lut))
    srcN = srcN.replace('{LENE}', str(lenE)).replace('{LENO1C}', str(LIMO1 - ORGO1)).replace('{LENO2C}', str(LIMO2 - ORGO2))
    blocks = [('A', srcA, ORGA, LIMA), ('B', SRCB, ORGB, LIMB), ('N', srcN, ORGN, LIMN),
              ('E', srcE, ORGE, LIME), ('O1', SRCO1, ORGO1, LIMO1), ('O2', SRCO2, ORGO2, LIMO2)]
    nm = {k: names(s) for k, s, _, _ in blocks}
    labs = {k: {n: 0 for n in nm[k]} for k, _, _, _ in blocks}
    for _ in range(10):
        out = {}; new = {}
        for k, src, org, lim in blocks:
            consts = {}
            for j, l in labs.items():
                if j != k: consts.update(l)
            code, L, a = assemble(COMMON + src, org, consts)
            out[k] = code; new[k] = {n: v for n, v in L.items() if n in nm[k]}
        if new == labs: break
        labs = new
    else:
        raise RuntimeError('etiquetas sin converger')
    for k, src, org, lim in blocks:
        assert org + len(out[k]) <= lim, ('bloque lleno', k, hex(org + len(out[k])), hex(lim))
    L = {}
    for l in labs.values(): L.update(l)
    assert L['LUT'] == ORGN and len(out['E']) == lenE
    return out, L, canvas, bg


def free(out):
    return {k: lim - org - len(out[k]) for k, org, lim in (('A', ORGA, LIMA), ('B', ORGB, LIMB), ('N', ORGN, LIMN),
                                                          ('E', ORGE, LIME), ('O1', ORGO1, LIMO1), ('O2', ORGO2, LIMO2))}


def patch(F, base, at, old, new):
    i = at - base
    assert bytes(F[i:i + len(old)]) == bytes(old), (hex(at), bytes(F[i:i + len(old)]).hex())
    F[i:i + len(new)] = bytes(new)


CUR = {}


def apply(F1, F2, F3):
    out, L, canvas, bg = CUR['build']
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
    p3(0xA521, [0x11, 0x98, 0xC2], [0xC3] + w(L['CROWDT']))
    p3(0xA0BF, [0xDD, 0x21, 0xAC, 0xD0], [0xC3] + w(L['WIPET']) + [0])
    p3(0xA0A1, [0xC3, 0x3A, 0xA5], [0xC3] + w(L['MENUY']))
    p3(0xA1E1, [0xCD, 0xBF, 0xA0], [0xCD] + w(L['RESTH']))
    p3(0x8538, [0xCD, 0xB5, 0x91], [0xCD] + w(L['RESUMH']))
    p3(0x8508, [0x21, 0xAF, 0x7E], [0xCD] + w(L['MENUZ']))
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
    out, L, canvas, bg = CUR['build']
    ca, cb = out['A'], out['B']
    o = bytearray(LIMA - 0xDD19)
    o[ORGA - 0xDD19:ORGA - 0xDD19 + len(ca)] = ca
    tail = cb[0xDD19 - ORGB:]
    o[0:len(tail)] = tail
    return o


def bank4(f3, f2=None):
    """banco 4 de la ROM: E, O1, O2 y el codigo original del menu (de la imagen final)"""
    out, L, canvas, bg = CUR['build']
    CUR['orig_O1'] = bytes(f3[ORGO1 - 0x84D0:LIMO1 - 0x84D0])
    CUR['orig_O2'] = bytes(f3[ORGO2 - 0x84D0:LIMO2 - 0x84D0])
    b = bytearray(b'\xff' * 0x4000)
    b[0:len(out['E'])] = out['E']
    assert len(out['E']) <= ROM_O1
    b[ROM_O1:ROM_O1 + len(out['O1'])] = out['O1']
    b[ROM_O2:ROM_O2 + len(out['O2'])] = out['O2']
    b[ROM_O1ORIG:ROM_O1ORIG + len(CUR['orig_O1'])] = CUR['orig_O1']
    b[ROM_O2ORIG:ROM_O2ORIG + len(CUR['orig_O2'])] = CUR['orig_O2']
    sbimg, ck = SA.sb_prerender()
    b[ROM_CK:ROM_CK + 288] = ck
    s2, d2 = f2
    b[ROM_MENU:ROM_MENU + 0xB40] = d2[0xC394 - s2:0xC394 - s2 + 0xB40]
    return bytes(b)
