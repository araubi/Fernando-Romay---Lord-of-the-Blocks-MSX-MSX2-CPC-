"""Reloj de posesion (30 segundos, reglas de 1984).
- Cada segundo de reloj de juego (1C96h, en la interrupcion, solo cuando corre el tiempo) se mira quien
  tiene el balon (bit 6 de (ix+1), el mismo del balon del marcador). Si cambia de dueno, o el balon queda
  suelto (tiro, rebote), vuelve a 30; si sigue el mismo, baja uno.
- Si llega a 0: la falta de CAMPO ATRAS del juego (saque para el otro), con el texto cambiado a POSESION!.
- Con 2 segundos o menos, la maquina (1 jugador) tira desde donde este: se le pulsa el disparo.
- Las cifras se pintan en el marcador (fila 22 de texto, que la salida de caracteres lleva al recuadro).
- Para hacer sitio, el historial de la repeticion guarda 3 vueltas menos (27 en lugar de 30)."""
T2 = 0x7085 - 3 * 0x4F          # nuevo tope del historial de la repeticion
SRC = """
; 1C96h: cada segundo del reloj del partido (interrupcion; solo A y HL)
PSEC:
  ld (110Ah),a
  ret c
  ld l,0
  ld a,(1130h)
  bit 6,a
  jr z,ps_1
  inc l
ps_1:
  ld a,(114Ah)
  bit 6,a
  jr z,ps_2
  ld l,2
ps_2:
  ld a,(PLAST)
  cp l
  ld a,l
  ld (PLAST),a
  jr nz,ps_r
  jp PSEC2
ps_r:
  ld a,30
  ld (PCNT),a
  or a
  ret
@@SPLIT@@
PSEC2:
  or a
  ret z
  ld a,(PCNT)
  or a
  ret z
  jp PSEC3
@@SPLIT@@
PSEC3:
  dec a
  ld (PCNT),a
  ret nz
  ld a,l
  ld (PVIOL),a
  or a
  ret
@@SPLIT@@
; 02D3h: tras pintar el tiempo: falta de posesion, texto y cifras
PPRINT:
  call 109Dh
  ld a,(PVIOL)
  or a
  jr z,pp_1
  ld ix,112Fh
  dec a
  jr z,pp_0
  ld ix,1149h
pp_0:
  xor a
  ld (PVIOL),a
  ld (PLAST),a
  ld a,(1124h)
  or a
  jr nz,pp_1
  call PTOG
  ld a,1
  ld (PSW),a
  ld e,5
  call 1687h
pp_1:
  jp PPRINT2
@@SPLIT@@
PPRINT2:
  ld a,(1124h)
  or a
  jr z,pp_r
  ld a,30
  ld (PCNT),a
  jr pp_2
pp_r:
  ld hl,PSW
  cp (hl)
  jr z,pp_2
  ld (hl),a
  call PTOG
pp_2:
  ld a,(PCNT)
  ld hl,PSHOWN
  cp (hl)
  ret z
  ld (hl),a
  jp PPRINT3
@@SPLIT@@
PPRINT3:
  ld b,2Fh
pp_3:
  inc b
  sub 10
  jr nc,pp_3
  add a,3Ah
  push af
  push bc
  ld a,2
  call 78B2h
  ld hl,1316h
  ld (0060h),hl
  pop bc
  ld a,b
  call 79C0h
  pop af
  jp 79C0h
@@SPLIT@@
; CAMPO ATRAS <-> POSESION!
PTOG:
  ld hl,11BFh
  ld de,PXS
  ld b,11
pt_1:
  ld a,(de)
  xor (hl)
  ld (hl),a
  inc hl
  inc de
  djnz pt_1
  ret
PXS: db {XS}
@@SPLIT@@
; 128Bh: control de la maquina; con 2 s o menos de posesion, disparo
PFIRE:
  ld a,(110Eh)
  or a
  jr z,pf_x
  ld a,(PLAST)
  cp 2
  jr nz,pf_x
  ld a,(PCNT)
  cp 3
  jr nc,pf_x
  ld a,(1147h)
  rla
  ld a,(85FBh)
  ret c
  or 10h
  ret
pf_x:
  ld a,(85FBh)
  ret
@@SPLIT@@
; 0FFFh: al montar la pantalla del partido, posesion a 30
PSETUP:
  call {SETUP}
  ld hl,PCNT
  ld (hl),30
  inc hl
  ld (hl),0
  ret
PCNT: db 30
PLAST: db 0
PVIOL: db 0
PSW: db 0
PSHOWN: db 30
"""
def apply(im):
    a = bytes(x ^ y for x, y in zip(b'CAMPO ATRAS', b' POSESION! '))
    assert im.rd(0x11BF, 11) == b'CAMPO ATRAS'
    w = lambda v: [v & 255, v >> 8]
    s = im.rd(0x0FFF, 3); assert s[0] == 0xCD
    src = SRC.replace('{XS}', ','.join(str(x) for x in a)).replace('{SETUP}', str(s[1] | s[2] << 8))
    # historial de la repeticion: 3 vueltas menos
    im.poke(0x2528, w(T2), w(0x7085))
    im.poke(0x2535, w(T2 - 0x6792), w(0x08F3))
    im.poke(0x254E, w(T2), w(0x7085))
    im.free.append([T2 + 0x4F, 0x70D4])
    L = im.place_many('shot', src.split('@@SPLIT@@'))
    im.poke(0x0FFF, [0xCD] + w(L['PSETUP']), s)
    im.poke(0x1C96, [0xCD] + w(L['PSEC']), [0x32, 0x0A, 0x11])
    im.poke(0x02D3, [0xCD] + w(L['PPRINT']), [0xCD, 0x9D, 0x10])
    im.poke(0x128B, [0xCD] + w(L['PFIRE']), [0x3A, 0xFB, 0x85])
