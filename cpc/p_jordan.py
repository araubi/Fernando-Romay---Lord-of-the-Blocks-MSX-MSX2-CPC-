"""NIVEL LEYENDA (cuarto nivel): en 1 jugador el rival es M. JORDAN (siempre el del campo derecho).
- Texto del nivel, dificultad de la maquina = NBA.
- Nombre M. JORDAN, cabezas propias (las del MSX2, ojos blancos) y piel oscura: al dibujar al jugador
  derecho, el color 3 (piel) pasa a 1 (negro) en el bucle de volcado de piezas (851Bh: LD C,A -> RST 28h).
- Capacidades: corre como Itu x1,1 x1,1 (paso extra 7 de cada 10), se recupera 1 de cada 3,
  punteria: distancia como Itu y error x0,9 x0,9."""
import pickle
from p_heads import pack
HEADS = pickle.load(open('/home/claude/cpc/jordan_heads.pkl', 'rb'))
COL = {'#': 1, 's': 1, 'w': 2, '.': 0, 'r': 1, 'k': 1}
# cabezas de Jordan con la silueta de las de Itu (asi encajan con el cuerpo); piel oscura y
# detalles en blanco (ojos y boca) para que se vea hacia donde mira
JL = [
"................", "................", "................",
"....#######.....",
"...########.....",
"...#########....",
"...#########....",
"...#w#######....",
"..##########....",
"...#########....",
"...ww#######....",
"....#######.....",
"....#######.....",
".....#####......",
".....####.......",
"......##........"]
JF = [
"................", "................", "................",
".....######.....",
"....########....",
"....########....",
"....########....",
"...##w####w##...",
"...##########...",
"...##########...",
"...####ww####...",
"....########....",
"....########....",
"....########....",
".....######.....",
"......####......"]
JB = [
"................", "................", "................",
".....######.....",
"....########....",
"....########....",
"....########....",
"...##########...",
"...##########...",
"...##########...",
"...##########...",
"....########....",
"....########....",
".....######.....",
".....######.....",
"................"]
JHEADS = {0x0A: JL, 0x16: [r[::-1] for r in JL], 0x22: JF, 0x2E: JB}
EVEN = JHEADS
def head_data(e, mirror=None):
    g = [[{'#': 1, 'w': 2, '.': 0}[ch] for ch in r] for r in JHEADS[e]]
    return bytes([16, 4]) + pack(g)
RST = [0x4F, 0x0F, 0x0F, 0x0F, 0x0F, 0xE6, 0x0F, 0x2F, 0xA1, 0x4F, 0xC9]   # en 0028h
SRC = """
; ---- texto y dificultad del nivel ----
LEVSTR:
  ld a,(10F6h)
  and 3
  ld de,23C3h
  ret z
  ld de,23CBh
  dec a
  ret z
  ld de,23D3h
  dec a
  ret z
  ld de,LEYTXT
  ret
LEVAI:
  ld a,(10F6h)
  and 3
  cp 3
  jr c,la_1
  ld a,2
la_1:
  sub 4
  neg
  dec a
  ret
@@SPLIT@@
; ---- 22A1h: tras elegir modo (y personaje) ----
JSELH:
  call SELH
  push hl
  xor a
  ld (JORDAN),a
  ld a,(10F6h)
  and 3
  cp 3
  jr nz,js_x
  ld a,(110Eh)
  or a
  jr z,js_x
  ld a,1
  ld (JORDAN),a
  ld hl,JNAME
  ld de,1182h
  ld bc,11
  ldir
  ld hl,66F4h + 2*0Ah
  ld de,JSAVE
  ld ix,JHT
  ld b,4
js_h:
  ld a,(hl)
  ld (de),a
  ld a,(ix+0)
  ld (hl),a
  inc hl
  inc de
  ld a,(hl)
  ld (de),a
  ld a,(ix+1)
  ld (hl),a
  inc ix
  inc ix
  inc de
  push de
  ld de,23
  add hl,de
  pop de
  djnz js_h
js_x:
  pop hl
  ret
; ---- 21EAh: entrada al menu ----
JMENUH:
  ld hl,RSTC
  ld de,0028h
  ld bc,11
  ldir
  ld a,4Fh
  ld (851Bh),a
  ld a,(JORDAN)
  or a
  jp z,MENUH
  xor a
  ld (JORDAN),a
  ld hl,JSAVE
  ld de,66F4h + 2*0Ah
  ld b,4
jm_1:
  ld a,(hl)
  ld (de),a
  inc hl
  inc de
  ld a,(hl)
  ld (de),a
  inc hl
  inc de
  push hl
  ld hl,22
  add hl,de
  ex de,hl
  pop hl
  djnz jm_1
  jp MENUH
; ---- 83F8h: color de la piel del jugador derecho ----
DRWSEL:
  ld hl,(0066h)
  ld a,(JORDAN)
  or a
  jr z,dw_n
  db 0DDh,7Dh
  cp 49h
  jr nz,dw_n
  db 0DDh,7Ch
  cp 11h
  jr nz,dw_n
  ld a,h
  cp 61h
  jr c,dw_y
  cp 70h
  jr c,dw_n
dw_y:
  ld a,0EFh
  ld (851Bh),a
  ret
dw_n:
  ld a,4Fh
  ld (851Bh),a
  ret
@@SPLIT@@
; ---- capacidades ----
JSPD:
  ld a,(JORDAN)
  or a
  jp z,SPD
  db 0DDh,7Dh
  cp 49h
  jp nz,SPD
  call 1B98h
  ret nz
  ld a,(JC1)
  inc a
  cp 10
  jr c,jp_1
  xor a
jp_1:
  ld (JC1),a
  cp 7
  jp c,SPEXT
  xor a
  ret
JTHR:
  ld a,(JORDAN)
  or a
  jp z,THR
  db 0DDh,7Dh
  cp 49h
  jp nz,THR
  ld a,(JC2)
  inc a
  cp 3
  jr c,jt_1
  xor a
jt_1:
  ld (JC2),a
  or a
  jr nz,jt_d
  bit 7,(ix+9)
  jr z,jt_d
  ld a,(ix+9)
  and 7Fh
  jr z,jt_d
  dec (ix+9)
jt_d:
  ld a,7
  ld b,a
  ret
JDIST:
  push af
  ld a,(JORDAN)
  or a
  jr z,jd_o
  ld a,(110Fh)
  rla
  jr c,jd_o
  pop af
  ld bc,50
  ret
jd_o:
  pop af
  jp DIST
JTOT:
  ld a,(JORDAN)
  or a
  jp z,TOT
  ld a,(110Fh)
  rla
  jp c,TOT
  ld bc,9
  call 77DBh
  ld bc,10
  call 77F2h
  ld bc,9
  call 77DBh
  ld bc,10
  call 77F2h
  ld a,r
  and 0Fh
  ret
@@SPLIT@@
JORDAN: db 0
JC1: db 0
JC2: db 0
JSAVE: ds 8
JHT: dw {JHT}
RSTC: db {RST}
JNAME: db ' M. JORDAN '
LEYTXT: db 'LEYENDA',0FFh
"""
def apply(im):
    from p_charsel import asm_str
    LH = {}
    for e in EVEN:
        L = im.place('jhead%02X' % e, 'JH%02X:\n db %s' % (e, ','.join(str(b) for b in head_data(e))))
        LH[e] = L['JH%02X' % e] - 0x32C8
    src = SRC.replace('{JHT}', ','.join(str(LH[e]) for e in (0x0A, 0x16, 0x22, 0x2E))).replace(
        '{RST}', ','.join(str(b) for b in RST))
    L = im.place_many('jordan', [asm_str(x) for x in src.split('@@SPLIT@@')])
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x2249, [0xCD] + w(L['LEVSTR']) + [0x18, 0x0E] + [0] * 14,
            [0x11, 0xC3, 0x23, 0x3A, 0xF6, 0x10, 0xE6, 0x03, 0x28, 0x09, 0x11, 0xCB, 0x23, 0x3D, 0x28, 0x03, 0x11, 0xD3, 0x23])
    im.poke(0x03EE, [0xCD] + w(L['LEVAI']) + [0x18, 0x05] + [0] * 5, [0x3A, 0xF6, 0x10, 0xE6, 0x03, 0xD6, 0x04, 0xED, 0x44, 0x3D])
    im.poke(0x22BB, [0xFE, 0x04], [0xFE, 0x03])
    im.free += [[0x224E, 0x225C], [0x03F3, 0x03F8]]       # resto de lo sustituido (se salta con el JR)
    im.poke(0x22A1, [0xCD] + w(L['JSELH']), [0xCD] + w(im.labels['SELH']))
    im.poke(0x21EA, [0xCD] + w(L['JMENUH']), [0xCD] + w(im.labels['MENUH']))
    im.poke(0x83F8, [0xCD] + w(L['DRWSEL']), [0x2A, 0x66, 0x00])
    for site in (0x1A42, 0x1A6B, 0x1AD1, 0x1B01):
        im.poke(site, [0xCD] + w(L['JSPD']), [0xCD] + w(im.labels['SPD']))
    im.poke(0x1C25, [0xCD] + w(L['JTHR']), [0xCD] + w(im.labels['THR']))
    im.poke(0x086E, [0xCD] + w(L['JDIST']), [0xCD] + w(im.labels['DIST']))
    im.poke(0x08BD, [0xCD] + w(L['JTOT']), [0xCD] + w(im.labels['TOT']))
