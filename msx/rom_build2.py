"""ROM MSX2 (ASCII16, 256 KB): bancos 0-3 juego + cargador; bancos 4-13 datos de color."""
from asm import assemble
from rom_build import cas_files
import msx2_data, msx2_sprite
DATA0 = 0x400
LDR = 0x8300

BOOT = """
  di
  ld a,(002Dh)
  or a
  jr nz,b_msx2
  ld hl,MSG
b_m:
  ld a,(hl)
  or a
  jr z,b_hang
  call 00A2h
  inc hl
  jr b_m
b_hang:
  di
  halt
b_msx2:
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
  push af
  ld hl,LDRSRC
  ld de,LDR
  ld bc,LDRLEN
  ldir
  pop af
  ld (SLOTV),a
  jp LDR
MSG:
  db 69,83,84,69,32,74,85,69,71,79,32,82,69,81,85,73,69,82,69,32,85,78,32,77,83,88,50,13,10,0
"""

LOADER = """
  ld sp,{LDR}
  ld a,1
  ld (0F3E9h),a
  ld (0F3EAh),a
  ld (0F3EBh),a
  ld a,4
  call 005Fh
  call 0062h
  ei
  ld a,{bank1}
  ld hl,{addr1}
  ld de,{st1}
  ld bc,{len1}
  call COPY
  call 0CF08h
  ld sp,{LDR}
  ei
  call SELROM
  ld a,(CURB)
  ld hl,(CURP)
  ld de,{st2}
  ld bc,{len2}
  call COPY
  call 0CF08h
  ld sp,{LDR}
  ei
  call SELROM
  ld a,(CURB)
  ld hl,(CURP)
  ld de,{st3}
  ld bc,{len3}
  call COPY
  ld a,(CURB)
  ld hl,(CURP)
  ld de,{stN}
  ld bc,{lenN}
  call COPY
  ld a,(SLOTV)
  ld ({romslot}),a
  ld sp,{LDR}
  ei
  jp 84D0h
SELROM:
  ld a,(SLOTV)
  ld h,40h
  call 0024h
  ret
COPY:
  ld (CURB),a
  ld (6000h),a
  ld (7000h),a
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

def build(img):
    files = cas_files(img)
    # cancha MSX2: fondo nuevo en el fichero 3 y tablas de color al banco 15
    import court2
    from court import court_bits, put_bits
    st, en, ex, d3 = files[2]; d3 = bytearray(d3)
    cfull, cvmap, cpack, cL = court2.tables(court_bits(d3), msx2_sprite.packcode())
    put_bits(d3, cfull); files[2] = (st, en, ex, bytes(d3))
    cn, L = msx2_sprite.blockN()
    blobs = [(st, data) for st, en, ex, data in files] + [(msx2_sprite.ORGN, cn)]
    pos = DATA0; p = {}
    for k, (st, data) in enumerate(blobs, 1):
        key = str(k) if k <= 3 else 'N'
        p['bank' + key] = pos // 0x4000; p['addr' + key] = 0x4000 + pos % 0x4000
        p['st' + key] = st; p['len' + key] = len(data); pos += len(data)
    assert pos <= 0x10000, hex(pos)
    p['LDR'] = LDR; p['romslot'] = L['ROMSLOT']
    lcode, LL, _ = assemble(LOADER.format(**p), LDR)
    assert LDR + len(lcode) <= 0x84D0
    boot_org = 0x4010
    bcode, BL, _ = assemble(BOOT, boot_org, {'LDR': LDR, 'LDRSRC': boot_org + 0x100, 'LDRLEN': len(lcode),
                                              'SLOTV': LL['SLOTV']})
    assert len(bcode) <= 0x100 and 0x110 + len(lcode) <= DATA0
    rom = bytearray(b'\xff' * 0x40000)
    rom[0:16] = b'AB' + bytes([boot_org & 255, boot_org >> 8]) + b'\0' * 12
    rom[0x10:0x10 + len(bcode)] = bcode
    rom[0x110:0x110 + len(lcode)] = lcode
    q = DATA0
    for st, data in blobs:
        rom[q:q + len(data)] = data; q += len(data)
    banks, last = msx2_data.build(4, 12)
    for b, data in banks.items(): rom[b * 0x4000:(b + 1) * 0x4000] = data
    assert last < 15
    # pista para la deteccion automatica del mapper en los emuladores (openMSX, WebMSX, blueMSX):
    # 'ld (77FFh),a' solo cuenta para ASCII16
    rom[15 * 0x4000 + 0x3E00:15 * 0x4000 + 0x3E00 + 3 * 64] = bytes([0x32, 0xFF, 0x77]) * 64
    rom[15 * 0x4000:15 * 0x4000 + len(cvmap)] = cvmap
    assert len(cvmap) <= 0x1000
    rom[15 * 0x4000 + 0x1000:15 * 0x4000 + 0x1000 + len(cpack)] = cpack
    s2 = cL['SEG2']; assert len(s2) <= 160 and len(cpack) <= 0x580
    s2 = s2.ljust(160, b'\0'); q, rr, ov, ov2 = msx2_sprite.packsegs()
    segs = s2 + q + rr + ov + ov2
    rom[15 * 0x4000 + 0x1580:15 * 0x4000 + 0x1580 + len(segs)] = segs
    assert 0x1580 + len(segs) <= msx2_sprite.MENUORIG
    zt = court2.zoom_table(cvmap)
    rom[15 * 0x4000 + msx2_sprite.ZOOMTAB:15 * 0x4000 + msx2_sprite.ZOOMTAB + len(zt)] = zt
    assert msx2_sprite.ZOOMTAB + len(zt) <= 0x3E00 
    o = msx2_sprite.OVL - 0x84D0; orig = files[2][3][o:o + msx2_sprite.OVLLEN]
    rom[15 * 0x4000 + msx2_sprite.MENUORIG:15 * 0x4000 + msx2_sprite.MENUORIG + len(orig)] = orig
    o2 = msx2_sprite.OVL2 - 0x84D0; orig2 = files[2][3][o2:o2 + msx2_sprite.OVL2LEN]
    assert msx2_sprite.MENUORIG + len(orig) <= msx2_sprite.MENUORIG2 and msx2_sprite.MENUORIG2 + len(orig2) <= msx2_sprite.ZOOMTAB
    rom[15 * 0x4000 + msx2_sprite.MENUORIG2:15 * 0x4000 + msx2_sprite.MENUORIG2 + len(orig2)] = orig2
    return bytes(rom), pos, last

if __name__ == '__main__':
    import sys
    from mk2 import make2
    img = make2(); open('msx2.cas', 'wb').write(img)
    rom, used, last = build(img)
    open(sys.argv[1] if len(sys.argv) > 1 else 'msx2.rom', 'wb').write(rom)
    print('ROM', len(rom), 'bytes; juego hasta %05X; datos de color hasta banco %d' % (used, last))
