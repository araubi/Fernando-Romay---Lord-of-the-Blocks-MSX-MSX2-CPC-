"""ROM de 64 KB con mapper ASCII16 a partir del CAS final.
Arranque (INIT en 4010h, pagina 1 = cartucho):
  - pagina 2 <- slot de la RAM de la pagina 3 (ENASLT)
  - copia el cargador a 8000h y salta alli (RAM)
Cargador (reproduce el BASIC del CAS: SCREEN 2, COLOR 1,1,1 y los tres BLOAD,R):
  - fichero 1 -> B3B0h.. , CALL CF08h  (presentacion)
  - fichero 2 -> 8534h.. , CALL CF08h  (stub: copia a pagina 1 y a E740h)
  - fichero 3 -> 84D0h.. , JP 84D0h
Entre llamadas vuelve a seleccionar el cartucho en la pagina 1 (los stubs cambian slots).
Los datos van seguidos desde el desplazamiento 400h de la ROM y se leen por la ventana 4000h-7FFFh
cambiando de banco escribiendo en 6000h."""
from asm import assemble
from common import cas_blocks

DATA0 = 0x400


def cas_files(cas):
    _, segs = cas_blocks(cas)
    out = []
    for ci in (3, 5, 7):
        c = segs[ci]; st = c[0] | c[1] << 8; en = c[2] | c[3] << 8; ex = c[4] | c[5] << 8
        out.append((st, en, ex, bytes(c[6:6 + en - st + 1])))
    return out


BOOT = """
  di
  ; slot de la pagina 3 (RAM) -> A ; se habilita en la pagina 2
  in a,(0A8h)
  rlca
  rlca
  and 3
  ld c,a
  ld b,0
  ld hl,0FCC1h
  add hl,bc
  ld a,(hl)
  and 80h
  jr z,b_p3
  ld a,(0FFFFh)
  cpl
  and 0C0h
  rrca
  rrca
  rrca
  rrca
  or 80h
b_p3:
  or c
  ld h,80h
  call 0024h
  ; slot propio (pagina 1)
  in a,(0A8h)
  rrca
  rrca
  and 3
  ld c,a
  ld b,0
  ld hl,0FCC1h
  add hl,bc
  ld a,(hl)
  and 80h
  jr z,b_p1
  ld hl,0FCC5h
  add hl,bc
  ld a,(hl)
  and 0Ch
  or 80h
b_p1:
  or c
  ld (MYSLOT),a
  ; copiar el cargador a la RAM y saltar
  ld hl,LDRSRC
  ld de,8000h
  ld bc,LDRLEN
  ldir
  jp 8000h
"""

LOADER = """
LOADER:
  ld sp,8300h
  ld a,(MYSLOT)
  ld (SLOTV),a
  ld a,1
  ld (0F3E9h),a
  ld (0F3EAh),a
  ld (0F3EBh),a
  ld a,2
  call 005Fh
  call 0062h
  ei
  ld a,{bank1}
  ld hl,{addr1}
  ld de,{st1}
  ld bc,{len1}
  call COPY
  call 0CF08h
  ld sp,8300h
  ei
  call SELROM
  ld a,(CURB)
  ld hl,(CURP)
  ld de,{st2}
  ld bc,{len2}
  call COPY
  call 0CF08h
  ld sp,8300h
  ei
  call SELROM
  ld a,(CURB)
  ld hl,(CURP)
  ld de,{st3}
  ld bc,{len3}
  call COPY
  ld sp,8300h
  ei
  jp 84D0h

SELROM:
  ld a,(SLOTV)
  ld h,40h
  call 0024h
  ret

; A=banco, HL=origen (4000h-7FFFh), DE=destino, BC=bytes
COPY:
  ld (CURB),a
  ld (6000h),a
  ld (7000h),a          ; sin efecto en la pagina 2 (es RAM); ayuda a detectar ASCII16
cp_l:
  ld a,(hl)
  ld (de),a
  inc de
  inc hl
  bit 7,h
  jr z,cp_n
  ld h,40h
  ld a,(CURB)
  inc a
  ld (CURB),a
  ld (6000h),a
cp_n:
  dec bc
  ld a,b
  or c
  jr nz,cp_l
  ld (CURP),hl
  ret
SLOTV: db 0
CURB:  db 0
CURP:  dw 0
"""


def build(cas):
    files = cas_files(cas)
    pos = DATA0; params = {}
    for k, (st, en, ex, data) in enumerate(files, 1):
        params['bank%d' % k] = pos // 0x4000
        params['addr%d' % k] = 0x4000 + pos % 0x4000
        params['st%d' % k] = st
        params['len%d' % k] = len(data)
        pos += len(data)
    assert pos <= 0x10000, hex(pos)
    assert [f[2] for f in files] == [0xCF08, 0xCF08, 0x84D0]
    lcode, LL, _ = assemble(LOADER.format(**params), 0x8000, {'MYSLOT': 0})
    # el arranque necesita LDRSRC/LDRLEN; MYSLOT es la variable SLOTV del cargador ya copiado? no:
    # el arranque guarda el slot en una variable de RAM fija antes de copiar -> usamos 8300h
    lcode, LL, _ = assemble(LOADER.format(**params), 0x8000, {'MYSLOT': 0x8300})
    boot_org = 0x4010
    for _ in range(3):
        bcode, BL, _ = assemble(BOOT, boot_org, {'MYSLOT': 0x8300, 'LDRSRC': boot_org + 0x100, 'LDRLEN': len(lcode)})
    assert len(bcode) <= 0x100 and 0x10 + 0x100 + len(lcode) <= DATA0
    rom = bytearray(b'\xff' * 0x10000)
    rom[0:16] = b'AB' + bytes([boot_org & 255, boot_org >> 8]) + b'\0' * 12
    rom[0x10:0x10 + len(bcode)] = bcode
    rom[0x110:0x110 + len(lcode)] = lcode
    p = DATA0
    for st, en, ex, data in files:
        rom[p:p + len(data)] = data; p += len(data)
    return bytes(rom), pos


if __name__ == '__main__':
    import sys
    rom, used = build(open(sys.argv[1], 'rb').read())
    open(sys.argv[2], 'wb').write(rom)
    print('ROM', len(rom), 'bytes; datos hasta %05X' % used)
