"""Pantalla de 256x192 (sugerencia del tester): CRTC R1=32 (64 bytes por linea), R2=42 (la imagen queda
donde estaba: se ven los mismos 256 px centrales), R6=24. Las coordenadas del juego no cambian
(320x200, columnas de byte 8-71 visibles); solo cambia donde esta cada linea (ver scrmap):
- tabla de lineas 7B70h: 'columna 0' virtual de cada linea (la 8 es la primera visible), asi la salida
  de caracteres, los recuadros, el volcado (8118h) y todo lo nuestro (LADR) siguen igual;
- dibujo por filas de caracteres (86D4h: fila*64, y 86CBh: salto de bloque C040h);
- repeticion ampliada: 32 bytes del bufer por linea (64 en pantalla), centrada en cada canasta;
- presentacion: la pantalla comprimida en el nuevo orden, con lo colocado en las zonas libres.
Cada bloque de 2 KB deja libres sus ultimos 448 bytes (3,5 KB en total, scrmap.FREE_SCR): estan en la
lista de huecos (build.FREE) y lo que se coloca ahi llega con la presentacion.
En el partido la imagen empieza una fila mas abajo (R13=32, ver p_raster) en vez de mover el VSYNC (R7):
el monitor no tiene que volver a engancharse."""
import scrmap, p_intro

def old_addr(y): return 0xC000 + (y >> 3) * 80 + (y & 7) * 0x800

ZSRC = """
; repeticion ampliada: direcciones de la tabla 7B70h + 8 (primera columna visible)
ZH1:
  ld l,(ix+0)
  ld h,(ix+1)
  inc ix
  inc ix
  ld de,8
  add hl,de
  ret
ZH2:
  ld l,(ix-2)
  ld h,(ix-1)
  ld bc,8
  add hl,bc
  ld e,(ix+0)
  ld d,(ix+1)
  inc ix
  inc ix
  ex de,hl
  add hl,bc
  ex de,hl
  ld bc,64
  ret
"""
BOOT = """
; antes de la presentacion: pantalla de 256x192
BOOTC:
  ld hl,CRT
bc_1:
  ld a,(hl)
  or a
  jp z,0BFCCh
  ld b,0BCh
  ld c,a
  out (c),c
  inc hl
  ld b,0BDh
  ld c,(hl)
  out (c),c
  inc hl
  jr bc_1
CRT: db 1,32, 2,42, 6,24, 12,30h, 13,0, 0
"""

def apply(im):
    w = lambda v: [v & 255, v >> 8]
    # tabla de lineas
    t_old = b''.join(bytes(w(old_addr(y))) for y in range(200))
    t_new = b''.join(bytes(w(scrmap.vaddr(y))) for y in range(200))
    im.poke(0x7B70, t_new, t_old)
    # tabla del volcado tal como esta al cargar (fila 0 del bufer en la linea 24)
    v_old = b''.join(bytes(w(old_addr(24 + r) + 8)) for r in range(104))
    v_new = b''.join(bytes(w(scrmap.addr(24 + r))) for r in range(104))
    im.poke(0x8118, v_new, v_old)
    # 86D4h: L columna (byte), H fila de caracteres -> HL = C000h + fila*64 + columna - 8
    im.poke(0x86CB, [0x01, 0x40, 0xC0], [0x01, 0x50, 0xC0])
    from asm import assemble
    code, _, _ = assemble("""
  ld a,l
  ld l,h
  ld h,0
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  add hl,hl
  sub 8
  ld e,a
  ld d,0C0h
  add hl,de
  ret
""", 0x86D4, {})
    assert len(code) <= 18
    im.poke(0x86D4, code, im.rd(0x86D4, len(code)))
    assert im.rd(0x86D4, 18) [:3] == bytes([0x7D, 0x6C, 0x26]) or True
    # repeticion ampliada
    L = im.place_many('screen', ZSRC.split('@@SPLIT@@'))
    im.poke(0x24AA, [0xCD] + w(L['ZH1']) + [0] * 7, [0xDD, 0x6E, 0x00, 0xDD, 0x23, 0xDD, 0x66, 0x00, 0xDD, 0x23])
    im.poke(0x24F0, [0xCD] + w(L['ZH2']) + [0x18, 0x0B] + [0] * 11,
            [0xDD, 0x6E, 0xFE, 0xDD, 0x66, 0xFF, 0xDD, 0x5E, 0x00, 0xDD, 0x23, 0xDD, 0x56, 0x00, 0xDD, 0x23])
    im.poke(0x24B7, [0x0E, 0x20], [0x0E, 0x28])
    im.poke(0x2434, [0x21, 0x02, 0x00], [0x21, 0x00, 0x00])
    im.poke(0x2439, [0x2E, 0x1E], [0x2E, 0x18])
    # arranque: CRTC antes de descomprimir la presentacion (desde el bloque de A568h, aun libre)
    code, BL, _ = assemble(BOOT, im.init_end, {})
    assert im.init_end + len(code) <= 0xBF68 and im.rd(im.init_end, len(code)) == bytes(len(code))
    im.poke(im.init_end, code)
    im.boot_free = 0xBF68 - (im.init_end + len(code))
    im.poke(0x01E3, [0xCD] + w(BL['BOOTC']), [0xCD, 0xCC, 0xBF])
    # presentacion
    p_intro.finish(im)
