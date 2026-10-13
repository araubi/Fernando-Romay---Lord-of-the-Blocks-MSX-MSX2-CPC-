"""VERSION MSX2 (SCREEN 4): relleno en color de ITURRIAGA y ROMAY con sprites modo 2, dos capas
(ropa/piel) combinadas por OR; colores por pixel leidos de la ROM (ver msx2_data.py).
Basado en sprite_patch (MSX1):
y volcado parcial de pantalla para que el juego no pierda velocidad.

Sprites:
- Mientras se dibujan las piezas de cada jugador se acumula su silueta (~mascara) en un plano
  de 32x48 px por jugador (8000h y 8100h, ya en el orden de los patrones de sprite 16x16).
- Al volcar: blanco = silueta AND pixel de fondo (0) de la imagen compuesta, asi la tinta del
  otro jugador o del balon queda encima. 6 sprites 16x16 por jugador, 2 por linea
  (4 con los dos jugadores juntos: el limite del TMS9918, sin parpadeo).
Volcado parcial (solo en el bucle principal, 8554h/8587h):
- Cada pieza marca las celdas 8x8 que toca (mapa en 8300h). Al empezar el fotograma solo se
  restauran desde el fondo las celdas dibujadas en el anterior; al acabar solo se envian a la
  VRAM las celdas dibujadas en este o en el anterior. 8 celdas por fotograma se refrescan siempre
  (rotando) como red de seguridad. Cualquier otra ruta de dibujo o un borrado de pantalla
  vuelve al volcado completo.
Codigo en E334h-E73Fh y DD19h-DE43h (se alarga el fichero 1; zonas que el juego no usa)."""
from asm import assemble
import re
import court2
CPACK = court2.CPACK
CPACKLEN = court2.PACK_LIMIT - court2.CPACK

ORG, LIMIT = 0xE334, 0xE700   # E700-E75F: ROWB (colores propios de la capa B)
ORG2, LIMIT2 = 0xDC18, 0xDE44      # incluye glifos 60h-7Fh de la fuente (no se usan; el cursor "_" 5Fh se conserva)
PLANEA0, PLANEB0, PLANEA1, PLANEB1 = 0xE800, 0xE900, 0xEA00, 0xEB00   # libres durante el partido
ROWA0, ROWA1 = 0xEC00, 0xEC30
SATBUF = 0xEC80
OVL2, OVL2LEN = 0xAC4F, 0xAF05 - 0xAC4F   # otra zona del menu
MENUORIG2 = 0x1D70
OVL, OVLLEN = 0xA53A, 0xA75F - 0xA53A    # codigo del menu: el partido la usa para codigo propio
ZOOMTAB = 0x2030                        # colores de la repeticion (6144 bytes)
MENUORIG = 0x1B40                       # copia del codigo original del menu en el banco 15
ORGN, LIMITN = 0x8000, 0x8230       # bloque nuevo, lo copia el cargador de la ROM
DMAP = 0x8300
ROWF = DMAP + 448
NBLK = 3                                 # bloques de 16 filas por jugador

ROW4 = '\n'.join(['  ld a,(de)', '  cpl', '  and (hl)', '  out (98h),a', '  ld (hl),b', '  inc l',
                  '  ex de,hl', '  add hl,bc', '  ex de,hl'] * 4)
UPLOAD8 = '\n'.join(['  ld a,(hl)', '  out (98h),a', '  add hl,de'] * 7 + ['  ld a,(hl)', '  out (98h),a'])

SRC = f"""
SATBUF   equ {SATBUF}
SATBNK   equ 823Eh
NOHIDE   equ 823Dh
CFNEED   equ 823Ch
SWAPPED  equ 8231h
OVR      equ 8239h
ZOOM     equ 823Bh
FA_R     equ 823Ah
MKV      equ 8256h
HSAME    equ 8257h
MCLO     equ 8258h
MCHI     equ 8259h
RLO      equ 8260h        ; 14 columnas minimas + 14 maximas (RHI = RLO+14)
; ---------- variables (se cargan con la cinta) ----------
ACTIVE:  db 0
SYNC:    db 0
FULLUP:  db 0
ROLL:    db 0
INIT:    db 0
DIRTY:   db 0
BANK:    db 0
; variables sin valor inicial (RAM libre 8240h..)
HSIG0    equ 8240h
HSIG1    equ 8243h
LASTIDX  equ 8246h
OWNER    equ 8247h
PST0     equ 8248h        ; valido, X0 (columna de byte), Y0 (fila del buffer)
PST1     equ 824Bh
FRONT    equ 824Eh

; ---------- 9E6Fh: recordar el indice de sprite ----------
IDXH:
  ld (LASTIDX),a
  add a,a
  ld l,a
  ld h,0
  ret

; ---------- B1F2h: copia completa del fondo (rutas que no son el bucle principal) ----------
NEWCOPY:
  xor a
  ld (SYNC),a
  ld a,(ZOOM)
  ld hl,NOHIDE
  or (hl)
  ld (hl),0
  call z,HIDE
  call SPRINIT
  ld hl,0B498h
  jp 0B1F5h

SPRINIT:
  ld a,(INIT)
  or a
  call z,PKLOAD
  ld a,(INIT)
  ld b,a
  ld a,(DIRTY)
  or a
  jr nz,nc_clr
  ld a,b
  or a
  jr nz,nc_ok
nc_clr:
  ld hl,{PLANEA0}
  ld de,{PLANEA0 + 1}
  ld bc,3FFh
  ld (hl),0
  ldir
  ld a,1
  ld (INIT),a
  xor a
  ld (DIRTY),a
nc_ok:
  ld a,(OVR)
  or a
  jr z,nc_o2
  ld hl,{ROWA0 - 0x500}
  ld de,{ROWA0 - 0x500 + 1}
  ld bc,95
  ld (hl),0
  ldir
  xor a
  ld (OVR),a
nc_o2:
  ld hl,{ROWA0}
  ld de,{ROWA0 + 1}
  ld bc,95
  ld (hl),0
  ldir
  ld a,1
  ld (ACTIVE),a
  xor a
  ld (PST0),a
  ld (PST1),a
  ret

; ---------- B1FEh: volcado completo + sprites ----------
NEWUPL:
  xor a
  ld (SYNC),a
FULLUPL:
  ld hl,0C298h
  call 0B201h
SPRUPL:
  ld a,(ACTIVE)
  or a
  jp z,HIDE
  call SPRPREP
  jp SATFL

; patrones al banco libre y tabla de atributos en SATBUF
SPRPREP:
  xor a
  ld (ACTIVE),a
  call R1SET
  ld a,(BANK)
  xor 3
  ld (BANK),a
  call UPALL
  xor a
  ld (DIRTY),a
  jp SATALL

SATOUT:
  call SATADR
  ld hl,SATBUF
  ld b,{NBLK * 32 + 1}
sat_out:
  ld a,(hl)
  out (98h),a
  inc hl
  djnz sat_out
  ret

HIDE:
  ld a,1
  call R14
  call HID1
  xor a
  call R14
HID1:
  call SATADR
  ld a,0D8h
  out (98h),a
  ret
R14:
  di
  out (99h),a
  ld a,8Eh
  out (99h),a
  ei
  ret

SATADR:
  di
  xor a
  out (99h),a
  ld a,5Eh
  out (99h),a
  ei
  ret

; ---------- D4CAh: borrado de pantalla -> ocultar sprites ----------
CLSH:
  xor a
  ld (SYNC),a
  ld (ZOOM),a
  call HIDE
  jp 0D501h

; ---------- patrones de un jugador (IY=PST, HL=plano, DE=VRAM) ----------
SPRPAT:
  ld a,(iy+0)
  or a
  ret z
  di
  ld a,e
  out (99h),a
  ld a,d
  or 40h
  out (99h),a
  ei
  push hl
  ld a,(iy+2)
  ld l,a
  rla
  sbc a,a
  ld h,a
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,(iy+1)
  ld e,a
  rla
  sbc a,a
  ld d,a
  add hl,de
  ld de,0C298h
  add hl,de
  ex de,hl
  pop hl
  ld bc,32
  ld a,{NBLK}
sp_blk:
  push af
  push de
  ld a,4
sp_col:
  push af
  push de
  call ROW16
  pop de
  inc de
  pop af
  dec a
  jr nz,sp_col
  pop de
  inc d
  inc d
  pop af
  dec a
  jr nz,sp_blk
  ret

ROW16:
  call ROW4
  call ROW4
  call ROW4
ROW4:
{ROW4}
  ret

; ---------- marcar rectangulo de celdas: E=fila, B=filas, D=col, C=columnas, valor en MKV ----------
MARKR:
  ld l,e
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,l
  add a,d
  ld l,a
  ld a,h
  adc a,{DMAP >> 8}
  ld h,a
  push de
  ld d,0
  ld iy,RLO
  add iy,de
  pop de
mr_row:
  ld a,(iy+0)
  cp d
  jr c,mr_1
  ld (iy+0),d
mr_1:
  ld a,d
  add a,c
  dec a
  cp (iy+14)
  jr c,mr_2
  ld (iy+14),a
mr_2:
  push hl
  push bc
  ld b,c
mr_c:
  ld a,(MKV)
  or (hl)
  ld (hl),a
  inc hl
  djnz mr_c
  pop bc
  pop hl
  ld a,l
  add a,32
  ld l,a
  jr nc,mr_3
  inc h
mr_3:
  inc iy
  djnz mr_row
  ret

; ---------- 8554h: inicio de fotograma del bucle principal ----------
MCOPY:
  ld a,(SYNC)
  or a
  jr nz,mc_sel
  ld a,1
  ld (NOHIDE),a
  call 0B1F2h
  call SETPAL
  ld a,(CFNEED)
  or a
  call nz,CFULL
  ld hl,{DMAP}
  ld de,{DMAP + 1}
  ld bc,447
  ld (hl),0
  ldir
  ld hl,RLO
  ld b,14
mc_i:
  ld (hl),0FFh
  inc hl
  djnz mc_i
  ld b,14
mc_i2:
  ld (hl),0
  inc hl
  djnz mc_i2
  ld a,1
  ld (FULLUP),a
  ret
mc_sel:
  call SPRINIT
  ; refresco rotativo: 8 celdas (fila ROLL/4, columnas (ROLL%4)*8..+7)
  ld a,1
  ld (MKV),a
  ld a,(ROLL)
  ld c,a
  rrca
  rrca
  and 3Fh
  ld e,a
  ld a,c
  and 3
  add a,a
  add a,a
  add a,a
  ld d,a
  ld bc,0108h
  call MARKR
  ; restaurar desde el fondo las celdas dibujadas en el fotograma anterior (por tramos)
  ld c,0
mc_row:
  ld hl,RLO
  ld b,0
  add hl,bc
  ld a,(hl)
  cp 32
  jp nc,mc_nx
  ld (MCLO),a
  ld (hl),0FFh
  ld de,14
  add hl,de
  ld a,(hl)
  ld (MCHI),a
  ld (hl),0
  ; HL = celda (fila C, columna MCLO)
  ld a,c
  rrca
  rrca
  rrca
  ld l,a
  and 1Fh
  add a,{DMAP >> 8}
  ld h,a
  ld a,l
  and 0E0h
  ld l,a
  ld a,(MCLO)
  ld e,a
  add a,l
  ld l,a
mc_cell:
  ld a,(MCHI)
  cp e
  jr c,mc_nx
  ld a,(hl)
  rra
  jr c,mc_run
  ld (hl),0
  inc hl
  inc e
  jr mc_cell
mc_run:
  ld d,0
mc_len:
  ld a,(hl)
  add a,a
  and 0Ah
  ld (hl),a
  inc hl
  inc e
  inc d
  ld a,(MCHI)
  cp e
  jr c,mc_le
  ld a,(hl)
  rra
  jr c,mc_len
mc_le:
  push hl
  push de
  ld a,e
  sub d
  ld e,a
  ld b,0
  ld hl,RLO
  add hl,bc
  ld a,(hl)
  cp e
  jr c,mc_r1
  ld (hl),e
mc_r1:
  ld a,l
  add a,14
  ld l,a
  ld a,e
  add a,d
  dec a
  cp (hl)
  jr c,mc_r2
  ld (hl),a
mc_r2:
  ld a,d
  ld (RK + 1),a
  ld a,32
  sub d
  ld (RS + 1),a
  ld a,c
  add a,0B4h
  ld h,a
  add a,0Eh
  ld d,a
  ld a,e
  add a,98h
  ld l,a
  ld e,a
  push bc
  ld ixl,8
mc_cp:
RK:
  ld bc,0
  ldir
RS:
  ld bc,0
  add hl,bc
  ex de,hl
  add hl,bc
  ex de,hl
  dec ixl
  jr nz,mc_cp
  pop bc
  pop de
  pop hl
  jr mc_cell
mc_nx:
  inc c
  ld a,c
  cp 14
  jp nz,mc_row
  ret

; ---------- 8587h: fin de fotograma del bucle principal ----------
MUPL:
  ld a,(FULLUP)
  or a
  jr z,mu_sel
  xor a
  ld (FULLUP),a
  call FULLUPL
  ld a,1
  ld (SYNC),a
  ret
mu_sel:
  call SPRPREP
  call SATBK
  ld a,20h
  call PASS
  halt
  call FLIP
  ld a,28h
  call PASS
  ld a,(ROLL)
  inc a
  cp 56
  jr c,mu_r
  xor a
mu_r:
  ld (ROLL),a
  ret

; A=20h (JR NZ): celdas sin jugador ; A=28h (JR Z): celdas con jugador (ahora o antes)
PASS:
  ld (PASSJ),a
  ld c,0
pa_row:
  ld hl,RLO
  ld b,0
  add hl,bc
  ld a,(hl)
  cp 32
  jr nc,pa_nx
  ld e,a                ; columna inicial
  ld a,l
  add a,14
  ld l,a
  ld a,(hl)
  sub e
  inc a
  ld b,a                ; numero de columnas
  ld a,c
  rrca
  rrca
  rrca
  ld l,a
  and 1Fh
  add a,{DMAP >> 8}
  ld h,a
  ld a,l
  and 0E0h
  add a,e
  ld l,a
  ld d,0                ; D=1 si la VRAM ya apunta a esta celda
pa_cell:
  ld a,(hl)
  or a
  jr z,pa_nr
  and 0Ch
PASSJ:
  jr nz,pa_nr
  push hl
  push bc
  ld a,d
  or a
  jr nz,pa_go
  ld a,e
  add a,a
  add a,a
  add a,a
  di
  out (99h),a
  ld a,c
  inc a
  or 40h
  out (99h),a
  ei
pa_go:
  ld a,c
  cp 7
  jr c,pa_go2
  call COURTC
  jr c,pa_slow
pa_go2:
  push de
  ld a,c
  add a,0C2h
  ld h,a
  ld a,e
  add a,98h
  ld l,a
  ld de,32
{UPLOAD8}
  pop de
  pop bc
  pop hl
  ld d,1
  jr pa_n
pa_slow:
  pop bc
  pop hl
pa_nr:
  ld d,0
pa_n:
  inc hl
  inc e
  djnz pa_cell
pa_nx:
  inc c
  ld a,c
  cp 14
  jp nz,pa_row
  ret
; ---- paleta del partido ----
SETPAL:
  ld hl,PALTAB
  ld b,8
SETPX:
sp_l:
  ld a,(hl)
  inc hl
  di
  out (99h),a
  ld a,90h
  out (99h),a
  ld a,(hl)
  inc hl
  out (9Ah),a
  ld a,(hl)
  inc hl
  out (9Ah),a
  ei
  djnz sp_l
  ret
PALTAB:
  db 2,71h,1
  db 3,73h,5
  db 6,16h,2
  db 12,73h,5
  db 14,71h,3
  db 4,74h,6
  db 11,35h,6
  db 13,44h,4


"""


SRCN = f"""
; ================= bloque nuevo (8000h, copiado por el cargador de la ROM) =================
ROMSLOT: db 0
SATBNK   equ 823Eh
NOHIDE   equ 823Dh
CFNEED   equ 823Ch
SAVA8    equ 8234h
ZOOM     equ 823Bh
CP_P:    db 0
CP_R:    db 0
CP_OFF:  db 0
CP_N:    db 0
CP_C0:   db 0
CP_S:    db 0
CP_CH:   db 0
CP_PL:   db 0
CP_CP:   dw 0
SP_PAT:  db 0
SP_FL:   db 0
SP_Y:    db 0
SP_B:    db 0
; ---- subir los 4 planos al banco de patrones (VRAM 3800h/3B00h) ----
UPALL:
  ld a,(BANK)
  add a,38h
  ld d,a
  ld e,0
  ld iy,PST0
  ld hl,{PLANEA0}
  push de
  call SPRPAT
  pop de
  push de
  ld hl,0C0h
  add hl,de
  ex de,hl
  ld hl,{PLANEB0}
  call SPRPAT
  pop de
  ld iy,PST1
  push de
  ld hl,180h
  add hl,de
  ex de,hl
  ld hl,{PLANEA1}
  call SPRPAT
  pop de
  ld hl,240h
  add hl,de
  ex de,hl
  ld hl,{PLANEB1}
  jp SPRPAT


; ---- cancha MSX2: mapa de colores (ROM banco 15) a la VRAM y paquete de la cancha a la RAM ----
CFULL:
  xor a
  ld (ZOOM),a
  ld (CFNEED),a
  call ROMON
  ld a,15
  ld (6000h),a
  xor a
  out (99h),a
  ld a,61h
  out (99h),a
  ld hl,4000h
  ld bc,3584
cf_l:
  ld a,(hl)
  out (98h),a
  inc hl
  dec bc
  ld a,b
  or c
  jr nz,cf_l
  jp ROMOFF

; ---- paquete de codigo y tablas a la RAM (ED00h..), una vez por entrada al partido ----
PKLOAD:
  ld a,1
  ld (CFNEED),a
  call ROMON
  ld a,15
  ld (6000h),a
  ld hl,5000h
  ld de,{CPACK}
  ld bc,{CPACKLEN}
  ldir
  ld de,{court2.SEG2}
  ld bc,160
  ldir
  ld de,0EC60h
  ld bc,32
  ldir
  ld de,0ECE2h
  ld bc,30
  ldir
  ld de,{OVL}
  ld bc,{OVLLEN}
  ldir
  ld de,{OVL2}
  ld bc,{OVL2LEN}
  ldir
  jp ROMOFF

; ---- entrada al menu (desde charsel MENUH): graficos del menu y paleta por defecto ----
MENUX:
  di
  call 0CF36h
  ei
  call MENUR
  xor a
  ld (INIT),a
  ld (ACTIVE),a
  ld (SATBNK),a
  ld a,3Fh
  ld (0D1C9h),a
  di
  out (99h),a
  ld a,85h
  out (99h),a
  ei
  ld hl,DEFTAB
  ld b,8
  jp SETPX



; ---- pagina 1 <- ROM del cartucho (DI); directo por A8h si el slot no es expandido ----
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

; ---- codigo original del menu (A53Ah..) desde la ROM: el partido usa esa zona para su codigo ----
MENUR:
  call ROMON
  ld a,15
  ld (6000h),a
  ld hl,{0x4000 + MENUORIG}
  ld de,{OVL}
  ld bc,{OVLLEN}
  ldir
  ld hl,{0x4000 + MENUORIG2}
  ld de,{OVL2}
  ld bc,{OVL2LEN}
  ldir
  jp ROMOFF
; A0A1h: entrada al menu desde el juego
MENUY:
  call MENUR
  jp {OVL}
; A19Bh: color de una celda de la cortinilla
WIPEH:
  ld a,(INIT)
  or a
  jp z,0A1A1h
  jp WIPEC

; ---- repeticion (vista ampliada): tabla de colores completa desde la ROM ----
ZOOMC:
  ld a,1
  ld (ZOOM),a
  ld (CFNEED),a
  call SETPAL
  call ROMON
  ld a,15
  ld (6000h),a
  xor a
  out (99h),a
  ld a,60h
  out (99h),a
  ld hl,{0x4000 + ZOOMTAB}
  ld bc,6144
zc_l:
  ld a,(hl)
  out (98h),a
  inc hl
  dec bc
  ld a,b
  or c
  jr nz,zc_l
  jp ROMOFF


; ---- A0BFh: cortinilla completa; al terminar, los sprites de color ya en su sitio ----
WIPEW:
  ld ix,0D0ACh
  ld c,31h
ww_l:
  call 0A0D0h
  call 0A132h
  halt
  dec c
  jr nz,ww_l
  jp SPRSHOW

; ---- caja de la grada (fila 1, 72 lineas): se redibuja toda la pantalla -> ocultar sprites ----
BXHID:
  ld a,(0D098h)
  cp 8
  ret nz
  ld a,(0D0A0h)
  cp 72
  ret nz
  jp HIDE

; ---- D27Ah (relleno de cajas): el color 17h de la cancha pasa a 14h (negro sobre parquet) ----
BXH:
  ld a,(0D1BCh)
  cp 1Fh
  call z,BXHID
  ld a,(0D1BCh)
  cp 17h
  jr nz,bx_1
  ld a,(0D0A0h)
  cp 48
  jr z,bx_c
  cp 80
  ld a,17h
  jr nz,bx_1
  call ZOOMC
  jr bx_sk
bx_c:
  call SETPAL
  call CFULL
  ld hl,0C298h
  call 0B201h
  call SPRSHOW
bx_sk:
  pop af
  pop hl
  ret
bx_1:
  ld h,a
  ld l,3Eh
  ret

; ---- R1: sprites 16x16, ampliados x2 en la repeticion ----
R1SET:
  ld a,(0D1C5h)
  and 0FCh
  or 2
  ld b,a
  ld a,(ZOOM)
  or a
  ld a,b
  jr z,r1_n
  or 1
r1_n:
  ld (0D1C5h),a
  di
  out (99h),a
  ld a,81h
  out (99h),a
  ei
  ret
; ---- A8F4h: dibujo de la repeticion; despues, sprites ampliados ----
ZENT:
  call ZBODY
SPRSHOW:
  ld a,(ACTIVE)
  or a
  call nz,SPRPREP
  jp SATFL
ZBODY:
  ld iy,0C398h
  jp 0A8F8h


; ---------- A521h: animacion del publico (escribe directo en el buffer) ----------
CROWD:
  push hl
  push iy
  ld a,(ACTIVE)
  or a
  jr z,cr_end
  ld a,1
  ld (MKV),a
  ld a,l
  and 1Fh
  ld d,a
  ld e,1
  ld bc,040Bh
  call MARKR
cr_end:
  pop iy
  pop hl
  ld de,0C298h
  ret


"""

SRC2 = f"""
; ---------- B01Ch: inicio de cada pieza: de que jugador es y origen de su plano ----------
PIECE:
  push ix
  pop hl
  ld a,1
  ld (MKV),a
  xor a
  ld (HSAME),a
  ld a,0FFh
  ld (OWNER),a
  ld a,(ACTIVE)
  or a
  jp z,pc_end
  ld a,(LASTIDX)
  cp 3Eh
  jr nc,pc_hoop
  ld a,h
  cp 94h
  jp nz,pc_end
  ld a,l
  ld hl,PST0
  ld b,0
  cp 0Bh
  jr z,pc_own
  ld hl,PST1
  inc b
  cp 25h
  jp nz,pc_end
pc_own:
  ld a,5
  ld (MKV),a
  ld a,b
  ld (OWNER),a
  ld (FRONT),a
  ld a,(hl)
  or a
  jp nz,pc_end
  ld (hl),1
  inc hl
  ld a,(0D099h)
  sra a
  sra a
  ld (hl),a
  inc hl
  ex de,hl
  ld hl,(0D09Ah)
  ld a,(hl)
  ld c,0
  cp 32
  jr c,pc_y
  ld c,1
  jr nz,pc_y
  ld c,9
pc_y:
  ld a,(0D098h)
  sub c
  ld (de),a
  ld a,1
  ld (DIRTY),a
  jp pc_end
pc_hoop:
  cp 48h
  jp nc,pc_end
  ld hl,HSIG0
  ld a,(0D099h)
  cp 64
  jr c,ph_1
  ld hl,HSIG1
ph_1:
  ld a,(LASTIDX)
  ld b,a
  ld a,(0D098h)
  ld c,a
  ld a,(0D099h)
  ld d,a
  push hl
  ld a,(hl)
  cp b
  jr nz,ph_new
  inc hl
  ld a,(hl)
  cp c
  jr nz,ph_new
  inc hl
  ld a,(hl)
  cp d
  jr nz,ph_new
  pop hl
  ld a,1
  ld (HSAME),a
  ; dibujo saltable si es un fotograma parcial y no se restauro ninguna de sus celdas
  ld a,(FULLUP)
  or a
  jr nz,pc_end
  ld a,(SYNC)
  or a
  jr z,pc_end
  ld hl,(0D09Ah)
  ld a,(0D098h)
  ld e,a
  add a,(hl)
  dec a
  rrca
  rrca
  rrca
  and 1Fh
  ld b,a
  ld a,e
  rrca
  rrca
  rrca
  and 1Fh
  ld e,a
  ld a,b
  sub e
  inc a
  ld b,a
  ld l,e
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,(0D099h)
  sra a
  sra a
  ld e,a
  ld d,0
  add hl,de
  ld de,{DMAP}
  add hl,de
  ld de,32
ph_r:
  ld a,(hl)
  inc hl
  or (hl)
  inc hl
  or (hl)
  inc hl
  or (hl)
  inc hl
  or (hl)
  and 2
  jr nz,pc_end
  add hl,de
  dec hl
  dec hl
  dec hl
  dec hl
  djnz ph_r
  pop hl
  ret
ph_new:
  pop hl
  ld (hl),b
  inc hl
  ld (hl),c
  inc hl
  ld (hl),d
pc_end:
  ld hl,(0D09Ah)
  ret

; ---------- B15Fh: por pieza (ya recortada): preparar seguimiento y marcar celdas ----------
MARK:
  ld a,(ACTIVE)
  or a
  jp z,mk_end
  ld a,(OWNER)
  cp 2
  call c,COMPOSE
mk_m:
  ; --- marcar celdas (los aros quietos no se marcan) ---
  ld a,(HSAME)
  or a
  jr nz,mk_end
  ld a,(0B1DFh)
  or a
  jr z,mk_end
  ld b,a
  ld a,(0B1E1h)
  or a
  jr z,mk_end
  ld c,a
  ld a,(0B1DEh)
  ld e,a
  add a,b
  dec a
  rrca
  rrca
  rrca
  and 1Fh
  ld d,a
  ld a,e
  rrca
  rrca
  rrca
  and 1Fh
  ld e,a
  ld a,d
  sub e
  inc a
  ld b,a
  ld a,(0B1E0h)
  ld d,a
  call MARKR
mk_end:
  ld a,(INIT)
  or a
  ld a,(0B1DFh)
  ret z
  pop hl
  jp FASTALL
DEFTAB:
  db 2,11h,6
  db 3,33h,7
  db 4,17h,1
  db 6,51h,1
  db 11,64h,6
  db 12,11h,4
  db 14,55h,5
  db 13,65h,2
"""


SRCP = f"""
; ================= codigo del paquete en RAM (ED00h.., lo carga PKLOAD desde la ROM) =================
PACKOK   equ 8233h
SAVA8    equ 8234h
CP_DP    equ 8235h
CP_KMIN  equ 8237h
CP_KMAX  equ 8238h
OVR      equ 8239h
; ---- composicion de una pieza de jugador en sus planos A/B (llamado desde MARK) ----
COMPOSE:
  ld a,(OWNER)
  ld (CP_P),a
  ld iy,PST0
  ld d,{PLANEA0 >> 8}
  or a
  jr z,cp_p0
  ld iy,PST1
  ld d,{PLANEA1 >> 8}
cp_p0:
  ld a,d
  ld (CP_PL),a
  ld a,(0B1DFh)
  or a
  ret z
  ld (CP_N),a
  ld a,(0B1DEh)
  sub (iy+2)
  ld (CP_R),a
  ld a,(0B1DEh)
  ld hl,0D098h
  sub (hl)
  ld (CP_OFF),a
  ld a,(0D099h)
  sra a
  sra a
  sub (iy+1)
  ld (CP_C0),a
  ; columnas visibles: kmin = max(0,-C0), kmax = min(3,3-C0)
  ld c,a
  ld b,0
  bit 7,a
  jr z,cp_k0
  neg
  ld b,a
cp_k0:
  ld a,b
  ld (CP_KMIN),a
  ld a,3
  sub c
  cp 4
  jr c,cp_k1
  ld a,3
cp_k1:
  ld (CP_KMAX),a
  ; sin recorte horizontal (kmin=0, kmax=3): saltar el recorte por fila
  xor 3
  or b
  ld a,cp_f2 - cp_clp - 2
  jr z,cp_k2
  xor a
cp_k2:
  ld (cp_clp + 1),a
  ld a,(0D099h)
  and 3
  ld (CP_S),a
  ld a,(SWAPPED)
  ld b,a
  ld a,(CP_P)
  xor b
  and 1
  ld (CP_CH),a
  call ROMON
  ld a,4
  ld (6000h),a
  ld a,(CP_CH)
  rrca
  rrca
  ld b,a
  ld a,(LASTIDX)
  add a,b
  ld l,a
  ld h,0
  add hl,hl
  add hl,hl
  ld a,(CP_S)
  add a,l
  ld l,a
  add hl,hl
  add hl,hl
  ld de,4000h
  add hl,de
  ld a,(hl)
  inc hl
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld c,(hl)
  ld (6000h),a
  push de
  ld a,(CP_OFF)
  ld l,a
  ld h,0
  add hl,de
  ld (CP_CP),hl
  pop hl
  ld b,0
  add hl,bc
  ex de,hl
  ld a,(CP_OFF)
  ld l,a
  ld h,0
  ld b,h
  ld c,l
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,bc
  add hl,de
  ld (CP_DP),hl
  ; ---- recorte vertical: filas r en [0, 48) ----
  ld a,(CP_R)
  bit 7,a
  jr z,cp_v1
  neg
  ld b,a
  ld a,(CP_N)
  sub b
  jp c,cp_end
  jp z,cp_end
  ld (CP_N),a
  ld c,b
  ld b,0
  ld hl,(CP_CP)
  add hl,bc
  ld (CP_CP),hl
  ld h,b
  ld l,c
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,bc
  ld bc,(CP_DP)
  add hl,bc
  ld (CP_DP),hl
  xor a
  ld (CP_R),a
cp_v1:
  cp {NBLK * 16}
  jp nc,cp_end
  ld b,a
  ld a,{NBLK * 16}
  sub b
  ld c,a
  ld a,(CP_N)
  cp c
  jr c,cp_v2
  ld a,c
cp_v2:
  ld (CP_N),a
  ; IXL = desplazamiento de fila dentro del plano: (r&15) + (r&30h)*4
  push ix
  ld a,b
  and 30h
  add a,a
  add a,a
  ld c,a
  ld a,b
  and 0Fh
  add a,c
  ld ixl,a
  ; registros alternativos: B'=filas, HL'=colores de fila, DE'=ROWA+r
  ld c,b
  ld hl,{ROWA0}
  ld a,(CP_P)
  or a
  jr z,cp_ra
  ld hl,{ROWA1}
cp_ra:
  ld a,c
  add a,l
  ld l,a
  ex de,hl
  ld hl,(CP_CP)
  ld a,(CP_N)
  ld b,a
  exx
  ld a,(CP_PL)
  ld d,a
  ld hl,(CP_DP)
cp_row:
  exx
  ld a,(hl)
  inc hl
  or a
  jr z,cp_nc
  cp 16
  jr nc,cp_ov
  ld (de),a
cp_nc:
  inc de
  exx
  jr cp_hd
cp_ov:
  ld c,a
  and 0Fh
  ld (de),a
  ld a,d
  sub 5
  ld d,a
  ld a,c
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  or 40h
  ld (de),a
  ld a,d
  add a,5
  ld d,a
  ld a,1
  ld (OVR),a
  inc de
  exx
cp_hd:
  push hl
  ld a,(hl)
  inc hl
  cp 0FFh
  jr z,cp_next
  ld c,a
  and 0Fh
  ld b,a
  ld a,c
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  ld c,a
cp_clp:
  jr cp_f2
  ld a,(CP_KMIN)
  cp b
  jr c,cp_f1
  ld b,a
cp_f1:
  ld a,(CP_KMAX)
  cp c
  jr nc,cp_f2
  ld c,a
cp_f2:
  ld a,c
  sub b
  jr c,cp_next
  inc a
  ld iyl,a
  ld a,b
  add a,a
  add a,l
  ld l,a
  jr nc,cp_f3
  inc h
cp_f3:
  ld a,(CP_C0)
  add a,b
  rlca
  rlca
  rlca
  rlca
  add a,ixl
  ld e,a
cp_k:
  ld c,(hl)
  inc hl
  ld a,(hl)
  or c
  jr z,cp_z
  cpl
  ld b,a
  ld a,(de)
  and b
  or c
  ld (de),a
  inc d
  ld a,(de)
  and b
  or (hl)
  ld (de),a
  dec d
cp_z:
  inc hl
  ld a,e
  add a,16
  ld e,a
  dec iyl
  jr nz,cp_k
cp_next:
  pop hl
  ld bc,9
  add hl,bc
  ld a,ixl
  inc a
  ld b,a
  and 0Fh
  ld a,b
  jr nz,cp_n1
  add a,48
cp_n1:
  ld ixl,a
  exx
  dec b
  exx
  jp nz,cp_row
  pop ix
cp_end:
  jp ROMOFF

; ================= volcado rapido de una pieza (sustituye B162h-B18Dh y B18Eh-B1DBh) =================
; A = filas; IX = tabla de direcciones de fila. Parametros leidos del codigo automodificado del juego.
FASTALL:
  or a
  ret z
  ld (FA_R),a
  ld a,(0B17Ch)
  or a
  jp z,fa_slow
  cp 5
  jp nc,fa_slow
  ld b,a
  ld a,4
  sub b
  ld b,a
  add a,a
  add a,a
  add a,a
  add a,b
  ld (fa_bj + 1),a
  ld a,(0B174h)
  ld (fa_off + 1),a
  ld hl,(0B179h)
  ld (fa_buf + 1),hl
  ld a,(0B180h)
  ld (fa_m + 1),a
  ld hl,(0B167h)
  ld de,0B18Eh
  or a
  sbc hl,de
  jr z,fa_sh
  ld a,(0B1D1h)
  ld (fu_n + 1),a
  ld hl,FA_CPU
  jr fa_go
fa_sh:
  ld a,(0B192h)
  cp 4
  jp nc,fa_slow
  ld (fs_w1 + 1),a
  ld (fs_w2 + 1),a
  ld b,a
  ld a,3
  sub b
  add a,a
  ld b,a
  add a,a
  add a,b
  ld (rr_j + 1),a
  ld (rd_j + 1),a
  ld a,(0B19Ah)
  ld (fs_f + 1),a
  ld a,(0B1A9h)
  ld hl,SH1
  dec a
  jr z,fa_s1
  ld hl,RRDP
  dec a
  jr z,fa_s1
  ld hl,SH3
fa_s1:
  ld (fs_c + 1),hl
  ld hl,FA_CPS
fa_go:
  ld (fa_cp + 1),hl
fa_row:
fa_cp:
  call 0
  ld l,(ix+0)
  inc ix
  ld h,(ix+0)
  inc ix
fa_off:
  ld de,0
  add hl,de
fa_buf:
  ld de,0
  ld b,d
fa_m:
  ld a,0
  add a,e
  ld c,a
fa_bj:
  jr fa_b0
fa_b0:
  ld a,(bc)
  and (hl)
  ex de,hl
  or (hl)
  ex de,hl
  ld (hl),a
  inc e
  inc c
  inc hl
  ld a,(bc)
  and (hl)
  ex de,hl
  or (hl)
  ex de,hl
  ld (hl),a
  inc e
  inc c
  inc hl
  ld a,(bc)
  and (hl)
  ex de,hl
  or (hl)
  ex de,hl
  ld (hl),a
  inc e
  inc c
  inc hl
  ld a,(bc)
  and (hl)
  ex de,hl
  or (hl)
  ex de,hl
  ld (hl),a
  ld hl,FA_R
  dec (hl)
  jr nz,fa_row
  ret
fa_slow:
  ld a,(0B1DFh)
  jp 0B162h
; copia con desplazamiento: datos, relleno, mascara, FFh; y desplazar la cadena 2w+2 bytes
FA_CPS:
  ld hl,(0D09Ah)
  ld de,0B1E4h
fs_w1:
  ld bc,0
  ldir
fs_f:
  ld a,0
  ld (de),a
  inc e
fs_w2:
  ld bc,0
  ldir
  ld a,0FFh
  ld (de),a
  ld (0D09Ah),hl
fs_c:
  jp 0
SH3:
  call RRDP
SH1:
  call RRP
RRP:
  ld hl,0B1E4h
  and a
rr_j:
  jr rr_0
rr_0:
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  inc l
  rr (hl)
  ret
"""


SRCQ = """
RRDP:
  ld hl,0B1E4h
  xor a
rd_j:
  jr rd_0
rd_0:
  rrd
  inc l
  rrd
  inc l
  rrd
  inc l
  rrd
  inc l
  rrd
  inc l
  rrd
  inc l
  rrd
  inc l
  rrd
  ret
"""

SRCR = """
; copia sin desplazamiento: 2w bytes (datos + mascara)
FA_CPU:
  ld hl,(0D09Ah)
  ld de,0B1E4h
fu_n:
  ld bc,0
  ldir
  ld (0D09Ah),hl
  ret
"""


SRCO = f"""
; ================= codigo en la zona del menu (A53Ah..), solo durante el partido =================
""" + court2.COURTC_SRC + f"""
; ---- tabla de colores de sprite (1C00h), 16 bytes por entrada de la SAT ----
CTOUT:
  ld a,1
  ld (CT_SK),a
  ld hl,SATBUF + 3
  ld b,{NBLK * 8}
ct_e:
  push bc
  push hl
  ld e,(hl)
  ld a,e
  and 80h
  ld d,a
  ld a,e
  and 3
  rlca
  rlca
  rlca
  rlca
  ld c,a
  bit 2,e
  ld hl,{ROWA0}
  jr z,ct_ab
  ld hl,{ROWA1}
ct_ab:
  ld a,l
  add a,c
  ld l,a
  ld b,16
  bit 6,e
  jr z,ct_aw
  ; capa B: piel (12 ITU / 3 ROMAY) o color propio de la fila (ROWB, solo si OVR)
  ld a,e
  rrca
  rrca
  and 1
  ld c,a
  ld a,(SWAPPED)
  xor c
  and 1
  ld a,12
  jr z,ct_bc
  ld a,3
ct_bc:
  or 40h
  or d
  ld c,a
  ; sin cambios respecto al fotograma anterior: no escribir
  ld a,(OVR)
  ld e,a
  ld a,(SATBNK)
  or a
  ld a,(OVRL)
  jr nz,ct_o1
  ld a,(OVRL + 1)
ct_o1:
  or e
  jr nz,ct_bw
  push hl
  call CTSH
  ld a,(hl)
  cp c
  ld (hl),c
  pop hl
  jr nz,ct_bw
  ld a,1
  ld (CT_SK),a
  jr ct_n
ct_bw:
  call CTAD
  ld a,(OVR)
  or a
  jr nz,ct_bs
  ld a,c
ct_bf:
  out (98h),a
  nop
  djnz ct_bf
  jr ct_n
ct_bs:
  ld a,h
  sub 5
  ld h,a
ct_bl:
  ld a,(hl)
  inc l
  or a
  jr z,ct_bd
  or d
  jr ct_bo
ct_bd:
  ld a,c
ct_bo:
  out (98h),a
  djnz ct_bl
  jr ct_n
ct_aw:
  call CTAD
ct_al:
  ld a,(hl)
  or d
  out (98h),a
  inc l
  djnz ct_al
ct_n:
  pop hl
  ld de,4
  add hl,de
  pop bc
  dec b
  jp nz,ct_e
  ld a,(OVR)
  ld b,a
  ld a,(SATBNK)
  or a
  ld a,b
  jr z,ct_o2
  ld (OVRL),a
  ret
ct_o2:
  ld (OVRL + 1),a
  ret
; HL <- sombra del sprite actual (indice = 24 - B de la pila)
CTSH:
  ld hl,7
  add hl,sp
  ld a,{NBLK * 8}
  sub (hl)
  ld hl,CT_SH
  push af
  ld a,(SATBNK)
  or a
  jr nz,cs_1
  ld hl,CT_SH + 24
cs_1:
  pop af
  add a,l
  ld l,a
  ret nc
  inc h
  ret
; direccion VRAM de la tabla de colores del sprite actual si se salto alguno
CTAD:
  ld a,(CT_SK)
  or a
  ret z
  push hl
  ld hl,7
  add hl,sp
  ld a,{NBLK * 8}
  sub (hl)
  pop hl
  push af
  rlca
  rlca
  rlca
  rlca
  and 0F0h
  di
  out (99h),a
  pop af
  rrca
  rrca
  rrca
  rrca
  and 0Fh
  or 5Ch
  out (99h),a
  ei
  xor a
  ld (CT_SK),a
  ret
CT_SK: db 0
OVRL:  db 0,0
CT_SH: ds 48


; ---- cortinilla (A19Bh): celda con los colores del mapa (filas 1..14) ----
WIPEC:
  ld a,(93E5h)
  or a
  jp nz,0A1A1h
  ld a,10h
  sub b
  cp 0Fh
  jp nc,0A1A1h
  dec a
  add a,40h
  ld h,a
  ld a,c
  dec a
  bit 7,(ix+0)
  jr z,wc_1
  ld a,20h
  sub c
wc_1:
  add a,a
  add a,a
  add a,a
  ld l,a
  push bc
  push hl
  call ROMON
  ld a,15
  ld (6000h),a
  pop hl
  ld b,8
wc_l:
  ld a,(hl)
  out (98h),a
  inc hl
  djnz wc_l
  pop bc
  jp ROMOFF
"""


SRCO2 = f"""

; ---- doble tabla de atributos/colores de sprite: 1E00h y 5E00h (R14=1); cambio con R5 ----
SATBK:
  ld a,(SATBNK)
  xor 1
  call R14
  call SATOUT
  call CTOUT
  xor a
  jp R14
SATFL:
  call SATBK
FLIP:
  ld a,(SATBNK)
  xor 1
  ld (SATBNK),a
  ld a,3Fh
  jr z,fl_0
  ld a,0BFh
fl_0:
  ld (0D1C9h),a
  di
  out (99h),a
  ld a,85h
  out (99h),a
  ei
  ret
; ---- tabla de atributos: jugador de delante primero; pares A (CC=0) / B (CC=1) ----
SATALL:
  push ix
  ld hl,SATBUF
  ld a,(FRONT)
  and 1
  push af
  call SATP2
  pop af
  xor 1
  call SATP2
  ld (hl),0D8h
  pop ix
  ret
SATP2:
  ld (CP_P),a
  ld iy,PST0
  or a
  jr z,s2_p
  ld iy,PST1
s2_p:
  ld a,(iy+0)
  or a
  jr nz,s2_vis
  ld b,{NBLK * 4}
s2_hid:
  ld (hl),0D9h
  inc hl
  ld (hl),0
  inc hl
  ld (hl),0
  inc hl
  ld (hl),0
  inc hl
  djnz s2_hid
  ret
s2_vis:
  ld a,(BANK)
  rrca
  rrca
  rrca
  ld c,a
  ld a,(CP_P)
  or a
  ld a,c
  jr z,s2_pb
  add a,48
s2_pb:
  ld (SP_PAT),a
  ld a,(CP_P)
  add a,a
  add a,a
  ld (SP_FL),a
  ld a,(ZOOM)
  or a
  ld a,(iy+2)
  jr nz,s2_z
  add a,7
  jr s2_y0
s2_z:
  add a,a
  sub 17
s2_y0:
  ld (SP_Y),a
  xor a
  ld (SP_B),a
s2_blk:
  xor a
  call S2ENT
  ld a,16
  call S2ENT
  ld a,(ZOOM)
  or a
  ld a,16
  jr z,s2_d
  add a,a
s2_d:
  ld b,a
  ld a,(SP_Y)
  add a,b
  ld (SP_Y),a
  ld a,(SP_B)
  inc a
  ld (SP_B),a
  cp {NBLK}
  jr nz,s2_blk
  ret
; A = desplazamiento X de la columna (0/16); HL = destino
S2ENT:
  call CALCX
  ld a,(SP_Y)
  jr nc,se2_on
  ld a,0D9h
se2_on:
  cp 0D8h
  jr nz,se2_y
  inc a
se2_y:
  ld d,a
  ld a,(SP_FL)
  ld e,a
  ld a,(SP_B)
  or e
  or b
  ld e,a
  ld a,(SP_PAT)
  ld b,a
  ld (hl),d
  inc hl
  ld (hl),c
  inc hl
  ld (hl),b
  inc hl
  ld (hl),e
  inc hl
  ld (hl),d
  inc hl
  ld (hl),c
  inc hl
  ld a,b
  add a,24
  ld (hl),a
  inc hl
  ld a,e
  or 40h
  ld (hl),a
  inc hl
  ld a,b
  add a,4
  ld (SP_PAT),a
  ret



; A = 0/16 -> C = X, B = EC (00/80h), acarreo = fuera de pantalla
CALCX:
  push hl
  ld e,a
  ld a,(iy+1)
  ld l,a
  rla
  sbc a,a
  ld h,a
  add hl,hl
  add hl,hl
  add hl,hl
  ld d,0
  add hl,de
  ld a,(ZOOM)
  or a
  jr z,cx_n
  add hl,hl
cx_n:
  ld b,0
  ld a,h
  or a
  jr z,cx_ok
  inc a
  jr nz,cx_off
  ld a,l
  cp 0E0h
  jr c,cx_off
  add a,32
  ld l,a
  ld b,80h
cx_ok:
  ld c,l
  pop hl
  or a
  ret
cx_off:
  ld c,0
  pop hl
  scf
  ret

"""


def names(src):
    return set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', src, re.M))


def build():
    """tres bloques con referencias cruzadas"""
    blocks = [(SRC, ORG, LIMIT), (SRC2, ORG2, LIMIT2), (SRCN, ORGN, LIMITN), (SRCP, court2.CODE, court2.MIX), (SRCQ, 0xEC60, 0xEC80), (SRCR, 0xECE2, 0xED00), (SRCO, OVL, OVL + OVLLEN), (SRCO2, OVL2, OVL2 + OVL2LEN)]
    nm = [names(b[0]) for b in blocks]
    labs = [{n: 0 for n in x} for x in nm]
    consts = {}
    for _ in range(6):
        codes = []; new = []; objs = []
        for k, (src, org, lim) in enumerate(blocks):
            cs = dict(consts)
            for j, l in enumerate(labs):
                if j != k: cs.update({a: b for a, b in l.items() if a not in nm[k]})
            code, L, a = assemble(src, org, cs)
            consts.update(a.consts)
            codes.append(code); new.append({n: v for n, v in L.items() if n in nm[k]}); objs.append(a)
        if new == labs: break
        labs = new
    for (src, org, lim), code in zip(blocks, codes):
        assert org + len(code) <= lim, (hex(org), hex(org + len(code)), hex(lim))
    L = {}
    for l in labs: L.update(l)
    return codes, L, objs


def patch3(F3, at, old, new):
    i = at - 0x84D0
    assert bytes(F3[i:i + len(old)]) == bytes(old), (hex(at), bytes(F3[i:i + len(old)]).hex())
    F3[i:i + len(new)] = bytes(new)


def apply(F1, F2, F3):
    _, L, _ = build()
    w = lambda v: [v & 255, v >> 8]
    patch3(F3, 0x9E6F, [0x87, 0x6F, 0x26, 0x00], [0xCD] + w(L['IDXH']) + [0x00])
    patch3(F3, 0xB01C, [0x2A, 0x9A, 0xD0], [0xCD] + w(L['PIECE']))
    patch3(F3, 0xB15F, [0x3A, 0xDF, 0xB1], [0xCD] + w(L['MARK']))
    patch3(F3, 0xB1F2, [0x21, 0x98, 0xB4], [0xC3] + w(L['NEWCOPY']))
    patch3(F3, 0xB1FE, [0x21, 0x98, 0xC2], [0xC3] + w(L['NEWUPL']))
    patch3(F3, 0x8554, [0xCD, 0xF2, 0xB1], [0xCD] + w(L['MCOPY']))
    patch3(F3, 0x8587, [0xCD, 0xFE, 0xB1], [0xCD] + w(L['MUPL']))
    patch3(F3, 0xA521, [0x11, 0x98, 0xC2], [0xCD] + w(L['CROWD']))
    patch3(F3, 0xA19B, [0xCD, 0xA1, 0xA1], [0xCD] + w(L['WIPEH']))      # cortinilla: colores del mapa
    patch3(F3, 0xA0A1, [0xC3, 0x3A, 0xA5], [0xC3] + w(L['MENUY']))      # entrada al menu
    patch3(F3, 0xA8F4, [0xFD, 0x21, 0x98], [0xC3] + w(L['ZENT']))      # repeticion: sprites ampliados
    patch3(F3, 0xA0BF, [0xDD, 0x21, 0xAC, 0xD0], [0xC3] + w(L['WIPEW']) + [0])   # cortinilla + sprites
    (ca, cb, cn, cp, cq, cr, co, co2), _, _ = build()
    head = cb[:0xDD19 - ORG2]                 # parte del bloque 2 dentro del fichero 1 (glifos sin uso)
    o = ORG2 - 0xB3B0; F1[o:o + len(head)] = head
    i = 0xD4CA - 0xB3B0                      # CLS_SCREEN2, en el fichero 1
    assert bytes(F1[i:i + 3]) == bytes([0xCD, 0x01, 0xD5])
    F1[i:i + 3] = bytes([0xCD] + w(L['CLSH']))
    i = 0xD27A - 0xB3B0                      # relleno de cajas: color de la cancha
    assert bytes(F1[i:i + 6]) == bytes([0x3A, 0xBC, 0xD1, 0x67, 0x2E, 0x3E])
    F1[i:i + 6] = bytes([0xCD] + w(L['BXH']) + [0, 0, 0])


def blockN():
    (ca, cb, cn, cp, cq, cr, co, co2), L, _ = build()
    return cn, L


def ext():
    """bytes que se anaden al final del fichero 1 (DD19h .. E73Fh)"""
    (ca, cb, cn, cp, cq, cr, co, co2), L, _ = build()
    out = bytearray(LIMIT - 0xDD19)
    out[ORG - 0xDD19:ORG - 0xDD19 + len(ca)] = ca
    tail = cb[0xDD19 - ORG2:]                 # lo que no cabe en el fichero 1 original
    out[0:len(tail)] = tail
    return out


def packcode():
    (ca, cb, cn, cp, cq, cr, co, co2), L, _ = build()
    return cp


def packsegs():
    (ca, cb, cn, cp, cq, cr, co, co2), L, _ = build()
    return cq.ljust(32, b'\0'), cr.ljust(30, b'\0'), co.ljust(OVLLEN, b'\0'), co2.ljust(OVL2LEN, b'\0')


if __name__ == '__main__':
    (ca, cb, cn, cp, cq, cr, co, co2), L, a = build()
    print('paquete', len(cp), 'fin %04X' % (court2.CODE + len(cp)))
    print(len(ca), 'fin %04X' % (ORG + len(ca)), '|', len(cb), 'fin %04X' % (ORG2 + len(cb)), '|', len(cn), 'fin %04X' % (ORGN + len(cn)))
    print({k: '%04X' % v for k, v in L.items() if k.isupper()})
