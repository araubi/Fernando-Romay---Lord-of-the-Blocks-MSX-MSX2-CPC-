"""Pantallas fuera del partido en SCREEN 5: presentacion coloreada, menu y descanso con los
jugadores en color (las mismas piezas del atlas que en la cancha).

Modo M (menu y descanso)
- El juego sigue dibujando su pantalla G2 en el banco 7 (la "sombra"). Las piezas de los jugadores
  (B01Ch) no se pintan en el bufer C298h: se apuntan en MLIST. Asi la sombra es solo el fondo.
- La primera vez (B1FEh tras entrar en el menu o el descanso) se convierte la sombra entera a G4 en la
  pagina 2 (fila a fila, con interrupciones entre filas), se muestra la pagina 2 y se copia a la 0 y la 1.
- Cada vuelta: se reconvierten las celdas marcadas (impresion de caracteres, D252h) y una fila de
  comprobacion rotativa (suma por celda); se restauran desde la pagina 2 los rectangulos de la pagina
  oculta y se dibujan las piezas con LMMM+TIMP; cambio de pagina en el VBLANK.
- El codigo y sus tablas viven en el banco 9 de la ROM y se ejecutan desde la pagina 1 con DI
  (RCALLM). Trabajo en RAM: el bufer B498h-C297h, que en esta version no usa nadie (COPYH lo salta).

Presentacion: banco 10. Imagen coloreada (RLE) en la pagina 0 y tira de fotogramas en la pagina 1;
CCE1h (dibujo de cada parte animada) copia el fotograma coloreado con HMMM."""
import numpy as np
from asm import assemble
import s5_assets as SA

MBANK, PBANK = 9, 10
JBANK = 11                 # 11: Jordan en los sitios de Romay, 12: en los de Itu; 13/14: originales
# RAM de trabajo (B498h-C297h)
PATB, COLB, MDIRT, MCK, MROWD = 0xB500, 0xB600, 0xB700, 0xBA00, 0xBD00
MLIST, MRL0, MRL1, MVARS = 0xBD20, 0xBD60, 0xBDE8, 0xBE70
NMLIST, NRL = 16, 32
# puntos de entrada fijos (tabla de saltos al principio del codigo de cada banco)
MCODE = 0x4600
ENT_M = ['MCONVR', 'MSTART', 'MFRAME', 'MMARKC', 'MMARKR']
ENT_P = ['PSTART', 'PFRAME', 'PSHOW']


def entries():
    d = {n: MCODE + 3 * i for i, n in enumerate(ENT_M)}
    d.update({n: 0x4000 + 3 * i for i, n in enumerate(ENT_P)})
    return d


CONSTS = f"""
PATB  equ {PATB}
COLB  equ {COLB}
MDIRT equ {MDIRT}
MCK   equ {MCK}
MROWD equ {MROWD}
MLIST equ {MLIST}
MRL0  equ {MRL0}
MRL1  equ {MRL1}
CVR   equ {MVARS + 0}
CVC   equ {MVARS + 1}
CVN   equ {MVARS + 2}
CVK   equ {MVARS + 3}
YOFF  equ {MVARS + 4}
RDN   equ {MVARS + 5}
PIDX  equ {MVARS + 6}
PSIDEV equ {MVARS + 7}
PY    equ {MVARS + 8}
PX2   equ {MVARS + 9}
RX    equ {MVARS + 10}
RY    equ {MVARS + 11}
RW2   equ {MVARS + 12}
RH    equ {MVARS + 13}
MR0   equ {MVARS + 14}
MR1   equ {MVARS + 15}
MC0   equ {MVARS + 16}
MC1   equ {MVARS + 17}
MDR   equ {MVARS + 18}
CVPB  equ {MVARS + 19}
SWAPPED equ 8231h
MT0   equ 4000h
CBB   equ 4400h
CXX   equ 4500h
"""

# rutinas del VDP sin EI (la ROM esta en la pagina 1: no puede entrar la interrupcion)
VDPR = """
RCMDLD:
  ld de,CMDB
  ld bc,15
  ldir
  ret
RVCMD:
  ld (CMDB+14),a
  call RVWAIT
  ld a,32
  out (99h),a
  ld a,91h
  out (99h),a
  ld hl,CMDB
  ld bc,0F9Bh
  otir
  ret
RVWAIT:
  ld a,2
  out (99h),a
  ld a,8Fh
  out (99h),a
rvw_l:
  in a,(99h)
  rra
  jr c,rvw_l
  xor a
  out (99h),a
  ld a,8Fh
  out (99h),a
  ret
RPAL:
  xor a
  out (99h),a
  ld a,90h
  out (99h),a
  ld hl,RPALS
  ld bc,209Ah
  otir
  ret
G4MODE:
  ; A = R2
  push af
  ld a,06h
  out (99h),a
  ld a,80h
  out (99h),a
  pop af
  out (99h),a
  ld a,82h
  out (99h),a
  jp RPAL
"""

SRCM = """
  jp MCONVR_
  jp MSTART_
  jp MFRAME_
  jp MMARKC_
  jp MMARKR_

; ---------- fila MROW entera -> pagina 2, sumas y marcas a cero ----------
MCONVR_:
  ld a,(MROW)
  ld d,a
  ld (CVR),a
  ld e,0
  ld b,32
  call RDCELLS
  xor a
  ld (CVC),a
  ld a,32
  ld (CVN),a
  call CONV
  ld a,(CVR)
  call CKROWP
  ld b,32
  call CKRUN
  ld a,(CVR)
  call DIRTROW
  ld b,32
mc_z:
  ld (hl),0
  inc hl
  djnz mc_z
  ld a,(CVR)
  ld l,a
  ld h,MROWD/256
  ld (hl),0
  ret

; ---------- pasar a G4: mostrar la pagina 2 y copiarla a la 0 y la 1 ----------
MSTART_:
  ld a,5Fh
  call G4MODE
  ld hl,FULLC
  call RCMDLD
  ld a,0D0h
  call RVCMD
  ld a,1
  ld (CMDB+7),a
  ld a,0D0h
  call RVCMD
  call RVWAIT
  xor a
  ld (DRAWPG),a
  ld (MRL0),a
  ld (MRL1),a
  ld (MRF0),a
  ld (MRF1),a
  ld (MROT),a
  ld (FLIPREQ),a
  inc a
  ld (MDISP),a
  ld (MPG2),a
  ret
FULLC:
  dw 0,512,0,0,256,192
  db 0,0,0

; ---------- una vuelta ----------
MFRAME_:
  ld a,(0B206h)
  add a,a
  add a,a
  add a,a
  ld (YOFF),a
  call MROTCHK
  call MDIRTY
  call MREST
  call MPIECES
  jp RVWAIT

; comprobacion rotativa: una fila por vuelta
MROTCHK:
  ld a,(MROT)
  cp 24
  jr c,mr_1
  xor a
mr_1:
  ld d,a
  ld (CVR),a
  inc a
  cp 24
  jr c,mr_2
  xor a
mr_2:
  ld (MROT),a
  ld e,0
  ld b,32
  call RDCELLS
  ld a,(CVR)
  call CKROWP
  ld e,0
mr_l:
  push hl
  call CKCELL
  pop hl
  cp (hl)
  jr z,mr_ok
  push hl
  ld bc,MDIRT-MCK+65536
  add hl,bc
  ld (hl),1
  ld a,(CVR)
  ld l,a
  ld h,MROWD/256
  ld (hl),1
  pop hl
mr_ok:
  inc hl
  ld a,e
  or a
  jr nz,mr_l
  ret

; celdas marcadas: tramos seguidos de cada fila
MDIRTY:
  xor a
  ld (MDR),a
md_r:
  ld a,(MDR)
  ld l,a
  ld h,MROWD/256
  ld a,(hl)
  or a
  jr z,md_nx
  ld (hl),0
  ld a,(MDR)
  ld (CVR),a
  call DIRTROW
  ld b,0
md_c:
  ld a,(hl)
  or a
  jr nz,md_run
  inc hl
  inc b
  ld a,b
  cp 32
  jr c,md_c
  jr md_nx
md_run:
  ld a,b
  ld (CVC),a
md_e:
  ld (hl),0
  inc hl
  inc b
  ld a,b
  cp 32
  jr nc,md_go
  ld a,(hl)
  or a
  jr nz,md_e
md_go:
  ld a,(CVC)
  ld c,a
  ld a,b
  sub c
  ld (CVN),a
  push bc
  push hl
  call RUNCONV
  pop hl
  pop bc
  ld a,b
  cp 32
  jr c,md_c
md_nx:
  ld a,(MDR)
  inc a
  ld (MDR),a
  cp 24
  jr c,md_r
  ret

; RUNCONV: tramo (CVR, CVC, CVN) -> pagina 2, sumas, rectangulo en las dos paginas
RUNCONV:
  ld a,(CVR)
  ld d,a
  ld a,(CVC)
  ld e,a
  ld a,(CVN)
  ld b,a
  call RDCELLS
  call CONV
  ld a,(CVR)
  call CKROWP
  ld a,(CVC)
  ld e,a
  ld d,0
  add hl,de
  ld a,(CVN)
  ld b,a
  call CKRUN
  ; las mismas celdas en las paginas 0 y 1 (las piezas que las pisen se restauran luego)
  xor a
  call CONVP
  ld a,2
  jp CONVP

; RADD: A = pagina; rectangulo (RX, RY, RW2 = ancho/2, RH)
RADD:
  ld hl,MRL0
  ld de,MRF0
  or a
  jr z,ra_1
  ld hl,MRL1
  ld de,MRF1
ra_1:
  ld a,(hl)
  cp NRL
  jr c,ra_2
  ld a,1
  ld (de),a
  ret
ra_2:
  inc (hl)
  inc hl
  add a,a
  add a,a
  ld e,a
  ld d,0
  add hl,de
  ld a,(RX)
  ld (hl),a
  inc hl
  ld a,(RY)
  ld (hl),a
  inc hl
  ld a,(RW2)
  ld (hl),a
  inc hl
  ld a,(RH)
  ld (hl),a
  ret

; restaurar los rectangulos de la pagina oculta desde la 2
MREST:
  ld a,(DRAWPG)
  or a
  ld hl,MRL0
  ld de,MRF0
  jr z,mt_1
  ld hl,MRL1
  ld de,MRF1
mt_1:
  ld a,(de)
  or a
  jr z,mt_2
  xor a
  ld (de),a
  ld (hl),a
  ld hl,FULLC
  call RCMDLD
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld a,0D0h
  jp RVCMD
mt_2:
  ld b,(hl)
  ld (hl),0
  inc hl
  ld a,b
  or a
  ret z
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+11),a
  ld (CMDB+12),a
  ld (CMDB+13),a
  ld a,2
  ld (CMDB+3),a
  ld a,(DRAWPG)
  ld (CMDB+7),a
mt_l:
  ld a,(hl)
  ld (CMDB+0),a
  ld (CMDB+4),a
  inc hl
  ld a,(hl)
  ld (CMDB+2),a
  ld (CMDB+6),a
  inc hl
  ld a,(hl)
  add a,a
  ld (CMDB+8),a
  ld a,0
  adc a,a
  ld (CMDB+9),a
  inc hl
  ld a,(hl)
  ld (CMDB+10),a
  inc hl
  push hl
  push bc
  ld a,0D0h
  call RVCMD
  pop bc
  pop hl
  djnz mt_l
  ret

; piezas apuntadas en esta vuelta
MPIECES:
  ld a,(MLISTN)
  or a
  ret z
  ld b,a
  xor a
  ld (MLISTN),a
  ld hl,MLIST
mp_l:
  push bc
  ld a,(hl)
  ld (PIDX),a
  inc hl
  ld a,(hl)
  ld (PSIDEV),a
  inc hl
  ld a,(hl)
  ld (PY),a
  inc hl
  ld a,(hl)
  ld (PX2),a
  inc hl
  push hl
  call MPIECE
  pop hl
  pop bc
  djnz mp_l
  ret

; una pieza (como S5PIECE, con el bufer empezando en la linea YOFF de la pantalla)
MPIECE:
  ld a,(PIDX)
  cp 3Eh
  jr nc,mq_sh
  ld c,a
  ld a,(PSIDEV)
  cp 25h
  ld b,0
  jr nz,mq_1
  inc b
mq_1:
  ld a,(SWAPPED)
  or a
  jr z,mq_2
  ld a,b
  xor 1
  ld b,a
  ld hl,RREMAP
  ld e,c
  ld d,0
  add hl,de
  ld c,(hl)
mq_2:
  ld a,b
  or a
  ld a,c
  jr z,mq_ent
  add a,62
  jr mq_ent
mq_sh:
  cp 4Ah
  ret nc
  add a,124-3Eh
mq_ent:
  ld c,a
  ld l,a
  ld h,0
  ld d,h
  ld e,l
  add hl,hl
  add hl,hl
  add hl,hl
  or a
  sbc hl,de
  ld de,RATAB
  ld a,(JATLAS)
  cp JBANK
  jr nz,mq_t
  ld a,c
  cp 62
  jr c,mq_t
  cp 124
  jr nc,mq_t
  ld de,RATABJ-62*7
mq_t:
  add hl,de
  push hl
  pop iy
  ld a,(iy+3)
  or a
  ret z
  ld a,(PX2)
  add a,a
  ret c
  add a,(iy+5)
  ret c
  ld (CMDB+4),a
  ld e,a
  ld d,(iy+3)
  add a,d
  jr nc,mq_w
  jr z,mq_w
  xor a
  sub e
  ld d,a
mq_w:
  ld a,d
  ld (CMDB+8),a
  ld a,(PY)
  ld l,a
  rla
  sbc a,a
  ld h,a
  ld a,(iy+6)
  add a,l
  ld l,a
  jr nc,mq_y1
  inc h
mq_y1:
  ld c,(iy+4)
  ld e,(iy+1)
  ld d,(iy+2)
  bit 7,h
  jr z,mq_top
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
  jr nc,mq_y2
  inc d
mq_y2:
  ld hl,0
mq_top:
  ld a,h
  or a
  ret nz
  ld a,l
  cp 112
  ret nc
  add a,c
  cp 113
  jr c,mq_bot
  ld a,112
  sub l
  ld c,a
mq_bot:
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
  ld a,(YOFF)
  add a,l
  ld (CMDB+6),a
  ld (RY),a
  ld a,(DRAWPG)
  ld (CMDB+7),a
  ld a,c
  ld (CMDB+10),a
  ld (RH),a
  ld a,(CMDB+4)
  and 0FEh
  ld (RX),a
  ld a,(CMDB+4)
  and 1
  inc a
  ld hl,CMDB+8
  add a,(hl)
  rra
  ld (RW2),a
  ld a,(DRAWPG)
  call RADD
  ld a,98h
  jp RVCMD

; ---------- marcas (desde los enganches de impresion y D252h) ----------
MMARKC_:
  ld a,(CROW)
  cp 24
  ret nc
  ld d,a
  ld a,(CCOL)
  ld e,a
  call MARK1
  dec e
  call MARK1
  jp MDIRTY
MARK1:
  ld a,e
  cp 32
  ret nc
  push de
  ld a,d
  call DIRTROW
  pop de
  push de
  ld d,0
  add hl,de
  ld (hl),1
  pop de
  ld l,d
  ld h,MROWD/256
  ld (hl),1
  ret

MMARKR_:
  ld a,(0D0A0h)
  or a
  ret z
  ld b,a
  ld a,(0D0A2h)
  or a
  ret z
  ld c,a
  ld a,(0D098h)
  ld l,a
  srl a
  srl a
  srl a
  ld (MR0),a
  ld a,l
  add a,b
  jr c,mm_big
  dec a
  srl a
  srl a
  srl a
  cp 24
  jr c,mm_r1
mm_big:
  ld a,23
mm_r1:
  ld (MR1),a
  ld a,(0D099h)
  ld (MC0),a
  add a,c
  dec a
  cp 32
  jr c,mm_c1
  ld a,31
mm_c1:
  ld (MC1),a
  ld a,(MR0)
mm_rl:
  cp 24
  jp nc,MDIRTY
  ld d,a
  ld a,(MC0)
  ld e,a
mm_cl:
  ld a,(MC1)
  cp e
  jr c,mm_rn
  push de
  call MARK1
  pop de
  inc e
  jr mm_cl
mm_rn:
  ld a,(MR1)
  cp d
  jp z,MDIRTY
  jp c,MDIRTY
  ld a,d
  inc a
  jr mm_rl

; ---------- conversion G2 -> G4 ----------
; RDCELLS: D = fila, E = columna, B = celdas -> patrones en PATB, colores en COLB
RDCELLS:
  ld a,b
  add a,a
  add a,a
  add a,a
  ld (RDN),a
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,e
  add a,a
  add a,a
  add a,a
  ld e,a
  out (99h),a
  ld a,d
  out (99h),a
  ld hl,PATB
  ld a,(RDN)
  ld b,a
  ld c,98h
rd_1:
  ini
  jp nz,rd_1
  ld a,e
  out (99h),a
  ld a,d
  or 20h
  out (99h),a
  ld hl,COLB
  ld a,(RDN)
  ld b,a
rd_2:
  ini
  jp nz,rd_2
  ret

; CONV: celdas leidas -> pagina 2 en (fila CVR, columna CVC), CVN celdas
CONV:
  ld a,4
CONVP:
  ld (CVPB),a
  xor a
  ld (CVK),a
cv_l:
  ld a,(CVR)
  add a,a
  add a,a
  add a,a
  ld hl,CVK
  add a,(hl)
  ld l,a
  rlca
  and 1
  ld h,a
  ld a,(CVPB)
  add a,h
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,l
  rrca
  and 80h
  ld h,a
  ld a,(CVC)
  add a,a
  add a,a
  or h
  out (99h),a
  ld a,l
  and 7Eh
  rrca
  or 40h
  out (99h),a
  ld a,(CVN)
  ex af,af'
  ld a,(CVK)
  ld e,a
  ld d,PATB/256
cv_c:
  inc d
  ld a,(de)
  ld l,a
  ld h,CBB/256
  ld b,(hl)
  inc h
  ld c,(hl)
  dec d
  ld a,(de)
  ld l,a
  ld h,MT0/256
  ld a,(hl)
  and c
  xor b
  out (98h),a
  inc h
  ld a,(hl)
  and c
  xor b
  out (98h),a
  inc h
  ld a,(hl)
  and c
  xor b
  out (98h),a
  inc h
  ld a,(hl)
  and c
  xor b
  out (98h),a
  ld a,e
  add a,8
  ld e,a
  ex af,af'
  dec a
  jr z,cv_n
  ex af,af'
  jr cv_c
cv_n:
  ld a,(CVK)
  inc a
  ld (CVK),a
  cp 8
  jr c,cv_l
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ret

; sumas de control: CKRUN (HL = destino, B celdas desde el principio del bufer)
CKRUN:
  ld e,0
ckn_l:
  push bc
  push hl
  call CKCELL
  pop hl
  pop bc
  ld (hl),a
  inc hl
  djnz ckn_l
  ret
; CKCELL: E = desplazamiento de la celda en PATB/COLB -> A ; E += 8
CKCELL:
  ld d,PATB/256
  ld c,0
  ld b,8
ck_1:
  ld a,(de)
  add a,c
  rlca
  ld c,a
  inc e
  djnz ck_1
  ld a,e
  sub 8
  ld e,a
  inc d
  ld b,8
ck_2:
  ld a,(de)
  add a,c
  rlca
  ld c,a
  inc e
  djnz ck_2
  ld a,c
  or 1
  ret

; A = fila -> HL = MCK + fila*32 ; DIRTROW -> MDIRT + fila*32
CKROWP:
  call ROWOFS
  ld de,MCK
  add hl,de
  ret
DIRTROW:
  call ROWOFS
  ld de,MDIRT
  add hl,de
  ret
ROWOFS:
  ld l,a
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  ret
"""

SRCP = """
  jp PSTART_
  jp PFRAME_
  jp PSHOW_

; imagen coloreada (pagina 0) y tira de fotogramas (pagina 1, y 256), luego G4
PSTART_:
  xor a
  ld hl,0
  ld de,PICA
  call PUP
  ld a,1
  ld hl,0
  ld de,PICB
  call PUP
  ld a,2
  ld hl,0
  ld de,PSTRIP
  call PUP
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
PSHOW_:
  ld a,1Fh
  call G4MODE
  ld a,1
  ld (MDISP),a
  ret
; PUP: A = R14, HL = direccion, DE = datos RLE
PUP:
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,l
  out (99h),a
  ld a,h
  or 40h
  out (99h),a
  ex de,hl
pu_l:
  ld a,(hl)
  inc hl
  or a
  ret z
  jp m,pu_r
  ld b,a
pu_t:
  ld a,(hl)
  out (98h),a
  inc hl
  djnz pu_t
  jr pu_l
pu_r:
  and 7Fh
  ld b,a
  ld a,(hl)
  inc hl
pu_s:
  out (98h),a
  nop
  djnz pu_s
  jr pu_l

; fotograma de la parte animada (D09Ah = datos del original) -> HMMM desde la tira
PFRAME_:
  ld de,(0D09Ah)
  ld hl,PFTAB
  ld b,NPF
pf_l:
  ld a,(hl)
  cp e
  jr nz,pf_n
  inc hl
  ld a,(hl)
  cp d
  jr z,pf_f
  dec hl
pf_n:
  inc hl
  inc hl
  inc hl
  inc hl
  djnz pf_l
  ret
pf_f:
  inc hl
  ld a,(hl)
  ld (CMDB+0),a
  inc hl
  ld a,(hl)
  ld (CMDB+2),a
  ld a,1
  ld (CMDB+3),a
  xor a
  ld (CMDB+1),a
  ld (CMDB+5),a
  ld (CMDB+7),a
  ld (CMDB+9),a
  ld (CMDB+11),a
  ld (CMDB+13),a
  ld a,(0D099h)
  add a,a
  add a,a
  add a,a
  ld (CMDB+4),a
  ld a,(0D098h)
  ld (CMDB+6),a
  ld a,(0D0A2h)
  add a,a
  add a,a
  add a,a
  ld (CMDB+8),a
  ld a,(0D0A0h)
  ld (CMDB+10),a
  ld a,0D0h
  call RVCMD
  jp RVWAIT
"""


def dbs(data, label=None):
    s = (label + ':\n') if label else ''
    return s + ''.join('  db ' + ','.join(str(b) for b in data[i:i + 16]) + '\n' for i in range(0, len(data), 16))


def tables():
    """MT0..MT3 (mascaras de cada par de pixeles), CBB (fondo doble), CXX (fondo xor tinta doble)"""
    lut = SA.g2lut()
    t = bytearray(0x600)
    for j in range(4):
        for p in range(256):
            hi = (p >> (7 - 2 * j)) & 1; lo = (p >> (6 - 2 * j)) & 1
            t[j * 256 + p] = (0xF0 if hi else 0) | (0x0F if lo else 0)
    for c in range(256):
        f, b = lut[c >> 4], lut[c & 15]
        t[0x400 + c] = (b << 4) | b
        x = f ^ b
        t[0x500 + c] = (x << 4) | x
    return bytes(t)


def bank_m(L, ent, remap, pal, jent):
    """banco 9: tablas (4000h-45FFh) + codigo (4600h)"""
    src = CONSTS + f'NRL equ {NRL}\nJBANK equ {JBANK}\n' + SRCM + VDPR + dbs(ent, 'RATAB') + dbs(jent, 'RATABJ') + dbs(remap, 'RREMAP') + dbs(pal, 'RPALS')
    consts = {k: v for k, v in L.items()}
    code, LL, _ = assemble(src, MCODE, consts)
    b = bytearray(b'\xff' * 0x4000)
    b[0:0x600] = tables()
    assert MCODE - 0x4000 + len(code) <= 0x4000
    b[MCODE - 0x4000:MCODE - 0x4000 + len(code)] = code
    return bytes(b), LL, len(code)


def bank_p(L, pal):
    import pres_color as PC
    st, pos, frames = PC.streams()
    tab = bytearray()
    for k, (x, y) in pos.items():
        tab += bytes([k & 255, k >> 8, x, y])
    src = (CONSTS + f'NPF equ {len(pos)}\n' + SRCP + VDPR + dbs(pal, 'RPALS') + dbs(tab, 'PFTAB') +
           dbs(st[0], 'PICA') + dbs(st[1], 'PICB') + dbs(st[2], 'PSTRIP'))
    code, LL, _ = assemble(src, 0x4000, dict(L))
    assert len(code) <= 0x4000, hex(len(code))
    return bytes(code) + b'\xff' * (0x4000 - len(code)), LL


# ---------------------------------------------------------------------------------------------
# bancos 11-14: piezas de Jordan / originales escritas en los rectangulos del atlas de un personaje
SRCJ = """
  jp JUPL
  jp JPAT
JPAT:
  ld hl,JATAB
  ld de,JADST
  ld bc,JALEN
  ld a,b
  or c
  ret z
  ldir
  ret
JUPL:
  ld hl,JRECTS
jr_n:
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld a,d
  cp 0FFh
  jr z,jr_e
  ld a,(hl)
  ld (JXB),a
  inc hl
  ld a,(hl)
  ld (JWB),a
  inc hl
  ld b,(hl)
  inc hl
jr_l:
  push bc
  ld a,e
  rla
  ld a,d
  rla
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,e
  rrca
  and 80h
  ld c,a
  ld a,(JXB)
  or c
  out (99h),a
  ld a,e
  and 7Eh
  rrca
  or 40h
  out (99h),a
  ld a,(JWB)
  ld b,a
jr_b:
  ld a,(hl)
  out (98h),a
  inc hl
  djnz jr_b
  inc de
  pop bc
  djnz jr_l
  jr jr_n
jr_e:
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ret
"""


def bank_j(items, atab=b'', adst=0):
    """items: [((x, y), img recortada)] -> banco con el codigo de subida (4000h) y el parche de la
    tabla del atlas (4003h: atab -> adst)"""
    data = bytearray()
    for (x, y), sub in items:
        h, w = sub.shape
        wb = (w + 1) // 2
        a = np.zeros((h, wb * 2), np.uint8); a[:, :w] = sub
        assert x % 2 == 0 and x // 2 + wb <= 128
        data += bytes([y & 255, y >> 8, x // 2, wb, h])
        data += bytes(((a[:, 0::2] << 4) | a[:, 1::2]).astype(np.uint8).flatten())
    data += bytes([0xFF, 0xFF])
    src = (CONSTS + f"JXB equ {MVARS + 24}\nJWB equ {MVARS + 25}\nJADST equ {adst}\nJALEN equ {len(atab)}\n" + SRCJ +
           dbs(atab, 'JATAB') + "JRECTS:\n")
    code, LL, _ = assemble(src, 0x4000, {})
    out = bytes(code) + bytes(data)
    assert len(out) <= 0x4000, hex(len(out))
    return out + b'\xff' * (0x4000 - len(out))


def slot_items(tab, imgs, ch):
    """piezas con la forma original colocadas en los rectangulos del personaje ch"""
    items = []
    for (c, i), (x, y, w, h, dx, dy) in sorted(tab.items(), key=lambda kv: str(kv[0])):
        if c != ch or i not in imgs: continue
        img = imgs[i]
        sub = img[dy:dy + h, dx:dx + w]
        rest = img.copy(); rest[dy:dy + h, dx:dx + w] = 0
        assert not rest.any(), ('pieza fuera del rectangulo', ch, hex(i))
        items.append(((x, y), sub))
    return items
