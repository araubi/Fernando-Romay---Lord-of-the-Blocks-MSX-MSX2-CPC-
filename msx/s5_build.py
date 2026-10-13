"""ROM MSX2 SCREEN 5 (ASCII16, 256 KB).
Bancos 0-3: arranque + cargador + ficheros del juego + bloque N; banco 4: bloque E (tablas del atlas);
bancos 5-8: VRAM inicial (fondo en la pagina 2 y atlas); banco 15: pista para detectar el mapper."""
import numpy as np
from asm import assemble
from rom_build import cas_files
import mk, charsel_patch, s5_patch, s5_assets as SA
from s5_pieces import Pieces
from court import court_bits
from rom_build2 import BOOT, DATA0, LDR

LOADER = """
  ld sp,{LDR}
  ld a,1
  ld (0F3E9h),a
  ld (0F3EAh),a
  ld (0F3EBh),a
  ld a,2
  call 005Fh
  call 0062h
  di
  ; G2 con las tablas en el banco 7 (1C000h), sprites desactivados
  ld hl,VREGS
vr_l:
  ld a,(hl)
  inc hl
  cp 0FFh
  jr z,vr_e
  ld b,a
  ld a,(hl)
  inc hl
  out (99h),a
  ld a,b
  or 80h
  out (99h),a
  jr vr_l
vr_e:
  ; tabla de nombres 1D800h = 0..255 x3 (R14 = 7 ya puesto)
  xor a
  out (99h),a
  ld a,18h + 40h
  out (99h),a
  ld bc,0300h
nt_l:
  ld a,c
  out (98h),a
  inc c
  jr nz,nt_l
  djnz nt_l
  ; VRAM inicial desde la ROM
  call SELROM
  ld hl,UPTAB
up_l:
  ld a,(hl)
  cp 0FFh
  jr z,up_e
  ld (6000h),a
  inc hl
  ld a,(hl)
  inc hl
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld c,(hl)
  inc hl
  ld b,(hl)
  inc hl
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,e
  out (99h),a
  ld a,d
  or 40h
  out (99h),a
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  push hl
  ex de,hl
up_c:
  ld a,(hl)
  out (98h),a
  inc hl
  dec bc
  ld a,b
  or c
  jr nz,up_c
  pop hl
  jr up_l
up_e:
  ld a,7
  out (99h),a
  ld a,8Eh
  out (99h),a
  ld a,0E0h
  out (99h),a
  ld a,81h
  out (99h),a
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
VREGS:
  db 0,02h, 1,0A0h, 2,76h, 3,0FFh, 4,3Bh, 5,36h, 6,07h, 7,04h, 8,0Ah, 10,07h, 14,07h, 15,0, 23,0, 0FFh
UPTAB:
{UPTAB}
  db 0FFh
SLOTV: db 0
CURB:  db 0
CURP:  dw 0
"""

# VRAM inicial: (banco de la ROM, direccion de VRAM, longitud) -> 16 KB por banco
UPLOADS = [(5, 0x10000, 0x4000), (6, 0x14000, 0x4000), (7, 0x18000, 0x4000), (8, 0x06000, 0x2000)]


def vram_image(bg, canvas):
    """bg: 192x256 indices ; canvas: y -> linea de 256 indices (atlas) -> bytearray 128K"""
    v = bytearray(0x20000)
    def put(y, line):
        a = y * 128
        for x in range(0, 256, 2): v[a + x // 2] = (int(line[x]) << 4) | int(line[x + 1])
    for y in range(192): put(512 + y, bg[y])
    sbimg, ck = SA.sb_prerender()
    for y in range(72): put(632 + y, sbimg[y])
    for y, line in canvas.items(): put(y, line)
    return v


def make_image(P):
    s5_patch.CUR['build'] = s5_patch.build(P)
    out, L, canvas, bg = s5_patch.CUR['build']
    charsel_patch.MSX2 = True; charsel_patch.MENUX_ADDR = L['MENUX']
    old = list(mk.mods)
    try:
        mk.mods[:] = [('s5_patch' if n == 'sprite_patch' else n) for n in old]
        return mk.make()
    finally:
        mk.mods[:] = old; charsel_patch.MSX2 = False


def build(ref_cas):
    P = Pieces(ref_cas)
    img = make_image(P)
    P = Pieces(img)                           # piezas de la imagen final (por si algun parche las cambia)
    img = make_image(P)
    out, L, canvas, bg = s5_patch.CUR['build']
    files = cas_files(img)
    blobs = [(st, data) for st, en, ex, data in files] + [(s5_patch.ORGN, out['N'])]
    pos = DATA0; p = {}
    for k, (st, data) in enumerate(blobs, 1):
        key = str(k) if k <= 3 else 'N'
        p['bank' + key] = pos // 0x4000; p['addr' + key] = 0x4000 + pos % 0x4000
        p['st' + key] = st; p['len' + key] = len(data); pos += len(data)
    assert pos <= 0x10000, hex(pos)
    # VRAM
    st3, en3, ex3, d3 = files[2]
    vram = vram_image(bg, canvas)
    up = []
    for bank, va, ln in UPLOADS:
        up.append('  db %d,%d\n  dw %d,%d,4000h' % (bank, va >> 14, va & 0x3FFF, ln))
    up.append('  db 8,%d\n  dw %d,%d,6000h' % (0x0E000 >> 14, 0x0E000 & 0x3FFF, 0x2000))
    p['UPTAB'] = '\n'.join(up)
    p['LDR'] = LDR; p['romslot'] = L['ROMSLOT']
    src = LOADER
    for k, v in p.items(): src = src.replace('{%s}' % k, str(v))
    lcode, LL, _ = assemble(src, LDR)
    assert LDR + len(lcode) <= 0x84D0, hex(LDR + len(lcode))
    boot_org = 0x4010
    bcode, BL, _ = assemble(BOOT, boot_org, {'LDR': LDR, 'LDRSRC': boot_org + 0x100, 'LDRLEN': len(lcode),
                                              'SLOTV': LL['SLOTV']})
    assert len(bcode) <= 0x100 and 0x110 + len(lcode) <= DATA0, (len(bcode), hex(0x110 + len(lcode)))
    rom = bytearray(b'\xff' * 0x40000)
    rom[0:16] = b'AB' + bytes([boot_org & 255, boot_org >> 8]) + b'\0' * 12
    rom[0x10:0x10 + len(bcode)] = bcode
    rom[0x110:0x110 + len(lcode)] = lcode
    q = DATA0
    for st, data in blobs:
        rom[q:q + len(data)] = data; q += len(data)
    rom[4 * 0x4000:5 * 0x4000] = s5_patch.bank4(d3)
    for bank, va, ln in UPLOADS:
        rom[bank * 0x4000:bank * 0x4000 + ln] = vram[va:va + ln]
    rom[8 * 0x4000 + 0x2000:9 * 0x4000] = vram[0x0E000:0x10000]
    rom[15 * 0x4000 + 0x3E00:15 * 0x4000 + 0x3E00 + 3 * 64] = bytes([0x32, 0xFF, 0x77]) * 64
    return bytes(rom), L, img, bg, vram


if __name__ == '__main__':
    import sys
    ref = open('/mnt/user-data/outputs/Fernando_Martin_Basket_Master_NIDAMIC.cas', 'rb').read()
    rom, L, img, bg, vram = build(ref)
    open(sys.argv[1] if len(sys.argv) > 1 else 's5.rom', 'wb').write(rom)
    open('s5.cas', 'wb').write(img)
    print('ROM', len(rom), {k: '%04X' % v for k, v in L.items() if k.isupper() and len(k) > 3})
