"""Relleno blanco de ITURRIAGA y ROMAY con sprites por hardware (modo hibrido MSX1)
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

ORG, LIMIT = 0xE334, 0xE740
ORG2, LIMIT2 = 0xDC18, 0xDE44      # incluye glifos 60h-7Fh de la fuente (no se usan; el cursor "_" 5Fh se conserva)
PLANE0, PLANE1 = 0x8000, 0x8100
SATBUF = 0x8200
DMAP = 0x8300
ROWF = DMAP + 448
NBLK = 3                                 # bloques de 16 filas por jugador

ROW4 = '\n'.join(['  ld a,(de)', '  cpl', '  and (hl)', '  out (98h),a', '  ld (hl),b', '  inc l',
                  '  ex de,hl', '  add hl,bc', '  ex de,hl'] * 4)
UPLOAD8 = '\n'.join(['  ld a,(hl)', '  out (98h),a', '  add hl,de'] * 7 + ['  ld a,(hl)', '  out (98h),a'])

SRC = f"""
SATBUF   equ {SATBUF}
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
RW_LEFT  equ 824Eh
MKLEFT   equ 824Fh

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
  call HIDE
  call SPRINIT
  ld hl,0B498h
  jp 0B1F5h

SPRINIT:
  ld a,(INIT)
  ld b,a
  ld a,(DIRTY)
  or a
  jr nz,nc_clr
  ld a,b
  or a
  jr nz,nc_ok
nc_clr:
  ld hl,{PLANE0}
  ld de,{PLANE0 + 1}
  ld bc,1FFh
  ld (hl),0
  ldir
  ld a,1
  ld (INIT),a
  xor a
  ld (DIRTY),a
nc_ok:
  ld a,1
  ld (ACTIVE),a
  xor a
  ld (PST0),a
  ld (PST1),a
  ld (RW_LEFT),a
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
  jp SATOUT

; patrones al banco libre y tabla de atributos en SATBUF
SPRPREP:
  xor a
  ld (ACTIVE),a
  ld (RW_LEFT),a
  ld a,(0D1C5h)
  or 2
  ld (0D1C5h),a
  di
  out (99h),a
  ld a,81h
  out (99h),a
  ei
  ld a,(BANK)
  xor 2
  ld (BANK),a
  add a,38h
  ld d,a
  ld e,0
  ld iy,PST0
  ld hl,{PLANE0}
  push de
  call SPRPAT
  pop de
  inc d
  ld iy,PST1
  ld hl,{PLANE1}
  call SPRPAT
  xor a
  ld (DIRTY),a
  ld a,(BANK)
  rrca
  rrca
  rrca
  ld c,a
  ld hl,SATBUF
  ld iy,PST0
  call SATP
  ld a,c
  add a,8
  ld c,a
  ld iy,PST1
  call SATP
  ld (hl),0D0h
  ret

SATOUT:
  call SATADR
  ld hl,SATBUF
  ld b,{NBLK * 16 + 1}
sat_out:
  ld a,(hl)
  out (98h),a
  inc hl
  djnz sat_out
  ret

HIDE:
  call SATADR
  ld a,0D0h
  out (98h),a
  ret

SATADR:
  di
  xor a
  out (99h),a
  ld a,5Bh
  out (99h),a
  ei
  ret

; ---------- D4CAh: borrado de pantalla -> ocultar sprites ----------
CLSH:
  xor a
  ld (SYNC),a
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

; ---------- entradas de atributos (IY=PST, HL=destino, C=patron base) ----------
SATP:
  ld a,(iy+0)
  or a
  jr nz,sa_vis
  ld b,{NBLK * 2}
sa_hid:
  ld (hl),0C0h
  inc hl
  inc hl
  inc hl
  inc hl
  djnz sa_hid
  ret
sa_vis:
  ld a,(iy+2)
  add a,7
  ld d,a
  ld b,{NBLK}
sa_row:
  ld e,0
  call SAENT
  ld e,16
  call SAENT
  ld a,d
  add a,16
  ld d,a
  djnz sa_row
  ret

; D=Y, E=desplazamiento X (0/16), C=patron; X real = X0*8+E con signo
SAENT:
  push bc
  push hl
  ld a,(iy+1)
  ld l,a
  rla
  sbc a,a
  ld h,a
  add hl,hl
  add hl,hl
  add hl,hl
  ld a,l
  add a,e
  ld c,a
  ld a,h
  adc a,0
  ld b,a
  pop hl
  ld e,0Fh
  or a
  jr z,se_ok
  inc a
  jr nz,se_hide
  ld a,c
  cp 0E0h
  jr c,se_hide
  add a,32
  ld c,a
  ld e,8Fh
se_ok:
  ld a,d
  cp 0D0h
  jr nz,se_y
  inc a
se_y:
  ld (hl),a
  inc hl
  ld (hl),c
  inc hl
  pop bc
  ld (hl),c
  inc hl
  ld (hl),e
  inc hl
  ld a,c
  add a,4
  ld c,a
  ret
se_hide:
  ld (hl),0C0h
  inc hl
  inc hl
  pop bc
  ld (hl),c
  inc hl
  ld (hl),0
  inc hl
  ld a,c
  add a,4
  ld c,a
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
  call 0B1F2h
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
  ld a,20h
  call PASS
  halt
  ld a,28h
  call PASS
  call SATOUT
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
  jr nz,pa_row
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

; ---------- B18Ah: tras dibujar cada fila de una pieza de jugador: silueta al plano ----------
ROWH:
  ld a,(RW_LEFT)
  or a
  jr z,rh_done
  dec a
  ld (RW_LEFT),a
RWM:
  ld hl,0
RWP:
  ld de,0
RWN:
  ld b,0
rh_l:
  ld a,(hl)
  cpl
  ex de,hl
  or (hl)
  ld (hl),a
  ld a,l
  add a,16
  ld l,a
  ex de,hl
  inc hl
  djnz rh_l
  ld hl,(RWP + 1)
  inc l
  ld a,l
  and 0Fh
  jr nz,rh_s
  ld a,l
  add a,48
  ld l,a
rh_s:
  ld (RWP + 1),hl
rh_done:
  pop bc
  dec b
  jp nz,0B165h
  ret

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

; ---------- B15Fh: por pieza (ya recortada): preparar seguimiento y marcar celdas ----------
MARK:
  xor a
  ld (RW_LEFT),a
  ld a,(ACTIVE)
  or a
  jp z,mk_end
  ; --- seguimiento de silueta para piezas de jugador ---
  ld a,(OWNER)
  cp 2
  jr nc,mk_m
  ld iy,PST0
  ld d,{PLANE0 >> 8}
  or a
  jr z,mk_p
  ld iy,PST1
  ld d,{PLANE1 >> 8}
mk_p:
  ld a,(0B1DEh)
  sub (iy+2)
  cp {NBLK * 16}
  jr nc,mk_m
  ld b,a                ; fila en el plano
  ld a,{NBLK * 16}
  sub b
  ld (MKLEFT),a
  ld a,b
  and 0Fh
  ld c,a
  ld a,b
  and 30h
  add a,a
  add a,a
  add a,c
  ld e,a                ; E = desplazamiento de fila en el plano (columna 0)
  ld a,(0B1E0h)
  sub (iy+1)            ; pc0
  ld c,0                ; kmin
  bit 7,a
  jr z,mk_k
  neg
  ld c,a
  xor a
mk_k:                   ; A = primera columna del plano, C = kmin
  cp 4
  jr nc,mk_m
  ld b,a
  ld a,4
  sub b
  ld h,a
  ld a,(0B1E1h)
  sub c
  jr c,mk_m
  jr z,mk_m
  cp h
  jr c,mk_n
  ld a,h
mk_n:
  ld (RWN + 1),a
  ld a,b
  add a,a
  add a,a
  add a,a
  add a,a
  add a,e
  ld e,a
  ld (RWP + 1),de
  ld hl,(0B179h)
  ld a,(0B180h)
  add a,c
  add a,l
  ld l,a
  jr nc,mk_q
  inc h
mk_q:
  ld (RWM + 1),hl
  ld a,(MKLEFT)
  ld (RW_LEFT),a
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
  ld a,(0B1DFh)
  ret
"""


def names(src):
    return set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', src, re.M))


def build():
    """dos bloques con referencias cruzadas"""
    na, nb = names(SRC), names(SRC2)
    la = {n: 0 for n in na}; lb = {n: 0 for n in nb}
    for _ in range(5):
        ca, la2, a = assemble(SRC, ORG, {k: v for k, v in lb.items() if k not in na})
        cb, lb2, b = assemble(SRC2, ORG2, dict({k: v for k, v in la2.items() if k not in nb}, **a.consts))
        if la2 == la and lb2 == lb: break
        la, lb = la2, lb2
    assert ORG + len(ca) <= LIMIT, hex(ORG + len(ca))
    assert ORG2 + len(cb) <= LIMIT2, hex(ORG2 + len(cb))
    L = dict(la); L.update(lb)
    return (ca, cb), L, (a, b)


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
    patch3(F3, 0xB18A, [0xC1, 0x10, 0xD8, 0xC9], [0xC3] + w(L['ROWH']) + [0x00])
    patch3(F3, 0xB1F2, [0x21, 0x98, 0xB4], [0xC3] + w(L['NEWCOPY']))
    patch3(F3, 0xB1FE, [0x21, 0x98, 0xC2], [0xC3] + w(L['NEWUPL']))
    patch3(F3, 0x8554, [0xCD, 0xF2, 0xB1], [0xCD] + w(L['MCOPY']))
    patch3(F3, 0x8587, [0xCD, 0xFE, 0xB1], [0xCD] + w(L['MUPL']))
    patch3(F3, 0xA521, [0x11, 0x98, 0xC2], [0xCD] + w(L['CROWD']))
    (ca, cb), _, _ = build()
    head = cb[:0xDD19 - ORG2]                 # parte del bloque 2 dentro del fichero 1 (glifos sin uso)
    o = ORG2 - 0xB3B0; F1[o:o + len(head)] = head
    i = 0xD4CA - 0xB3B0                      # CLS_SCREEN2, en el fichero 1
    assert bytes(F1[i:i + 3]) == bytes([0xCD, 0x01, 0xD5])
    F1[i:i + 3] = bytes([0xCD] + w(L['CLSH']))


def ext():
    """bytes que se anaden al final del fichero 1 (DD19h .. E73Fh)"""
    (ca, cb), L, _ = build()
    out = bytearray(LIMIT - 0xDD19)
    out[ORG - 0xDD19:ORG - 0xDD19 + len(ca)] = ca
    tail = cb[0xDD19 - ORG2:]                 # lo que no cabe en el fichero 1 original
    out[0:len(tail)] = tail
    return out


if __name__ == '__main__':
    (ca, cb), L, a = build()
    print(len(ca), 'bytes, fin %04X' % (ORG + len(ca)), '|', len(cb), 'bytes, fin %04X' % (ORG2 + len(cb)))
    print({k: '%04X' % v for k, v in L.items() if k.isupper()})
