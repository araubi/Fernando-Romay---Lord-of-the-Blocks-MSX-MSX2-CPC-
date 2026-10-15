"""Capacidades por jugador (como en MSX). ITURRIAGA (IX=112Fh): +10% velocidad, se cansa un 10% antes.
F. ROMAY (IX=1149h): -10% velocidad, se cansa un 20% mas lento.
Punteria: ITURRIAGA error x0,9; F. ROMAY termino de distancia x55/70 en vez de x50/70.
(110Fh bit 7 = tira el jugador 1)"""
SRC = """
SPD:
  call 1B98h
  ret nz
  db 0DDh,7Dh            ; ld a,ixl
SPDCP:
  cp 2Fh
  jr z,sp_p1
  ld a,(CNT2)
  inc a
  cp 5
  jr c,sp_1
  xor a
sp_1:
  ld (CNT2),a
  and a
  jr z,sp_skip
  xor a
  ret
sp_skip:
  inc a
  ret
sp_p1:
  ld a,(CNT1)
  inc a
  cp 5
  jr c,sp_2
  xor a
sp_2:
  ld (CNT1),a
  and a
  jr nz,sp_done
SPEXT:
  ex (sp),hl
  ld a,l
  ex (sp),hl
  cp 45h
  jr z,sp_dl
  cp 6Eh
  jr z,sp_il
  cp 0D4h
  jr z,sp_dh
  inc h
  jr sp_done
sp_dl:
  dec l
  jr sp_done
sp_il:
  inc l
  jr sp_done
sp_dh:
  dec h
sp_done:
  xor a
  ret
THR:
  db 0DDh,7Dh
THRCP:
  cp 2Fh
  jr z,th_1
  ld a,(CNT4)
  inc a
  cp 5
  jr c,th_a
  xor a
th_a:
  ld (CNT4),a
  and a
  jr nz,th_done
  bit 7,(ix+9)
  jr z,th_done
  ld a,(ix+9)
  and 7Fh
  jr z,th_done
  dec (ix+9)
  jr th_done
th_1:
  ld a,(CNT3)
  inc a
  cp 10
  jr c,th_b
  xor a
th_b:
  ld (CNT3),a
  and a
  jr nz,th_done
  bit 7,(ix+9)
  jr z,th_done
  inc (ix+9)
th_done:
  ld a,7
  ld b,a
  ret
DIST:
  ld bc,50
  push af
  ld a,(110Fh)
  rla
DIJR:
  jr c,di_1
  ld c,55
di_1:
  pop af
  ret
TOT:
  ld a,(110Fh)
  rla
TOJR:
  jr nc,to_1
  ld bc,9
  call 77DBh
  ld bc,10
  call 77F2h
to_1:
  ld a,r
  and 0Fh
  ret
CNT1: db 0
CNT2: db 0
CNT3: db 0
CNT4: db 0
"""
def apply(im):
    L = im.place('stats', SRC)
    w = lambda v: [v & 255, v >> 8]
    for site in (0x1A42, 0x1A6B, 0x1AD1, 0x1B01):
        im.poke(site, [0xCD] + w(L['SPD']), [0xCD, 0x98, 0x1B])
    im.poke(0x1C25, [0xCD] + w(L['THR']), [0x3E, 0x07, 0x47])
    im.poke(0x086E, [0xCD] + w(L['DIST']), [0x01, 0x32, 0x00])
    im.poke(0x08BD, [0xCD] + w(L['TOT']) + [0], [0xED, 0x5F, 0xE6, 0x0F])
