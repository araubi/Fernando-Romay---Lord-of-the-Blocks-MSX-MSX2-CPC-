"""Controles: J1 cursores + ESPACIO (y joystick 1); J2 W/S/A/D + SHIFT; pausa P (antes 6).
Reescribe la lectura de 85FCh (mascaras en 85FAh/85FBh: bit0 vertical, bit1 abajo, bit2 horizontal,
bit3 derecha, bit4 disparo). Matriz de teclado copiada en 00CCh-00D5h (fila 0..9, 0 = pulsada)."""
SRC = """
  org 85FCh
INPUT:
  ld a,(0D5h)            ; joystick 0: b0 arriba b1 abajo b2 izq b3 der b4 fuego2 b5 fuego1
  cpl
  ld c,a
  and 1Fh
  bit 5,c
  jr z,in_1
  or 10h
in_1:
  ld c,a
  ld a,(0CCh)            ; fila 0: cursores arriba(0) derecha(1) abajo(2)
  rra
  jr c,in_2
  set 0,c
in_2:
  rra
  jr c,in_3
  set 3,c
in_3:
  rra
  jr c,in_4
  set 1,c
in_4:
  ld a,(0CDh)            ; fila 1: cursor izquierda (0)
  rra
  jr c,in_5
  set 2,c
in_5:
  ld a,(0D1h)            ; fila 5: espacio (7)
  rla
  jr c,in_6
  set 4,c
in_6:
  call ENC
  ld (85FAh),a
  ld c,0
  ld a,(0D3h)            ; fila 7: W(3) S(4) D(5)
  bit 3,a
  jr nz,in_7
  set 0,c
in_7:
  bit 4,a
  jr nz,in_8
  set 1,c
in_8:
  bit 5,a
  jr nz,in_9
  set 3,c
in_9:
  ld a,(0D4h)            ; fila 8: A(5)
  bit 5,a
  jr nz,in_10
  set 2,c
in_10:
  ld a,(0CEh)            ; fila 2: SHIFT(5)
  bit 5,a
  jr nz,in_11
  set 4,c
in_11:
  call ENC
  ld (85FBh),a
  ret
; C: b0 arriba b1 abajo b2 izq b3 der b4 fuego -> A codificado
ENC:
  xor a
  bit 1,c
  jr z,en_1
  or 3
  jr en_2
en_1:
  bit 0,c
  jr z,en_2
  or 1
en_2:
  bit 3,c
  jr z,en_3
  or 0Ch
  jr en_4
en_3:
  bit 2,c
  jr z,en_4
  or 4
en_4:
  bit 4,c
  ret z
  or 10h
  ret
"""
def apply(im):
    from asm import assemble
    code, L, _ = assemble(SRC, 0)
    assert 0x85FC + len(code) <= 0x8685, len(code)
    im.poke(0x85FC, code, [0x11, 0xD5, 0x00])
    im.poke(0x02D9, [0x3E, 0x1B], [0x3E, 0x30])     # pausa: P (fila 3 bit 3)
