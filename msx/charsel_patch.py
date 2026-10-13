"""Seleccion de personaje en "1 JUGADOR": submenu JUGADOR 1 / 1 - ITU / 2 - ROMAY.
El humano juega siempre en el campo izquierdo; si elige a Romay se intercambian en tiempo de
ejecucion: cabezas (tabla de sprites), fotogramas de salto/tiro/mate (en espejo), nombres y
capacidades (velocidad, energia y punteria). Al volver al menu todo vuelve a su estado normal.

El codigo vive en huecos de RAM 8000h-84CFh que el juego no usa; como esa zona la ocupa BASIC
durante la carga, se guarda en el area de repeticiones (DE44h..) y una rutina de arranque
(enganchada en 84E8h) lo copia antes de que el juego use esa area."""
import re
from asm import assemble

STAGE = 0xDE44                    # area de repeticiones: intacta hasta el primer partido
# huecos de RAM libres en tiempo de juego (ver sprite_patch)
FRAGS = [(0x827C, 0x82F0), (0xF280, 0xF380)]     # F280-F37F: nunca usado (por debajo del area de la BIOS)
DATA = 0x84C0                     # TMP(6) + ITUNAME(10)
SWAPPED, NSW = 0x8231, 0x8232     # banderas (en 8231-823F, libre)

# capacidades: bytes que se conmutan con XOR (direccion, valor)
TOGGLES = [(0xD0D7, 0x2E), (0xD11A, 0x2E), (0xAFA2, 0x08), (0xAFAC, 0x08)]

COMMON = f"""
TMP      equ {DATA}
ITUNAME  equ {DATA + 6}
SWAPPED  equ {SWAPPED}
NSW      equ {NSW}
PRINTS   equ 9397h
BOXFILL  equ 0D247h
WAITKEY  equ 0D7C7h
"""

# rutinas (cada una se coloca en un hueco)
R_SWAP = """
; ---- intercambio de personajes (se aplica dos veces = vuelve al estado normal) ----
SWAPCH:
  ; cabezas: entradas de tabla (0A,0B) (16,17) (22,23) (2E,2F)
  ld hl,7760h + 2*0Ah
  ld b,4
sw_h:
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld c,(hl)
  inc hl
  ld a,(hl)
  ld (hl),d
  dec hl
  ld (hl),e
  dec hl
  ld (hl),a
  dec hl
  ld (hl),c
  ld de,24
  add hl,de
  djnz sw_h
  ; saltos: (30..32 , +3) y (36..39 , +4)
  ld c,30h
  ld b,3
sw_j1:
  push bc
  ld a,c
  add a,3
  call MIRSW
  pop bc
  inc c
  djnz sw_j1
  ld c,36h
  ld b,4
sw_j2:
  push bc
  ld a,c
  add a,4
  call MIRSW
  pop bc
  inc c
  djnz sw_j2
  ; capacidades
  ld hl,TOGTAB
  ld b,4
sw_t:
  ld e,(hl)
  inc hl
  ld d,(hl)
  inc hl
  ld a,(de)
  xor (hl)
  ld (de),a
  inc hl
  djnz sw_t
  ld a,(SWAPPED)
  xor 1
  ld (SWAPPED),a
  ret
"""

R_MIR = """
; ---- C, A = indices de sprite: a <- espejo(b), b <- espejo(a), 40 filas de 6 bytes ----
MIRSW:
  call SPADR
  push hl
  ld a,c
  call SPADR
  pop de                ; DE = datos de b, HL = datos de a
  ld b,40
ms_r:
  push bc
  push de
  push hl
  ld de,TMP
  ld bc,6
  ldir                  ; TMP = fila de a
  pop de                ; DE = fila de a
  pop hl                ; HL = fila de b
  push hl
  push de
  call MIRCPY           ; a = espejo(b)
  pop hl
  ld bc,6
  add hl,bc
  ex de,hl              ; DE = siguiente fila de a
  pop hl                ; HL = fila de b
  push de
  push hl
  ex de,hl              ; DE = fila de b
  ld hl,TMP
  call MIRCPY           ; b = espejo(TMP)
  pop hl
  ld bc,6
  add hl,bc
  ex de,hl              ; DE = siguiente fila de b
  pop hl                ; HL = siguiente fila de a
  pop bc
  djnz ms_r
  ret
; direccion de los datos del sprite A -> HL
SPADR:
  add a,a
  ld l,a
  ld h,0
  ld de,7760h
  add hl,de
  ld e,(hl)
  inc hl
  ld d,(hl)
  ld hl,415Ah + 2
  add hl,de
  ret
"""

R_MCPY = """
; ---- DE <- espejo de la fila HL (3 bytes datos + 3 mascara) ----
MIRCPY:
  call mc_h
mc_h:
  inc hl
  inc hl
  ld c,3
mc_b:
  ld a,(hl)
  push bc
  ld b,8
  ld c,a
mc_rv:
  rr c
  rla
  djnz mc_rv
  pop bc
  ld (de),a
  inc de
  dec hl
  dec c
  jr nz,mc_b
  inc hl
  inc hl
  inc hl
  inc hl
  ret
TOGTAB:
""" + '\n'.join('  dw %d\n  db %d' % t for t in TOGGLES) + "\n"

R_SEL = """
; ---- A6C7h: tras elegir 1 o 2 jugadores en el menu ----
SELH:
  ld a,1
  ld (0B206h),a
  ld a,(93EAh)
  or a
  ret z
  ld hl,0660h
  ld (0D098h),hl
  ld hl,0050h
  ld (0D0A0h),hl
  ld l,14h
  ld (0D0A2h),hl
  ld a,0F1h
  ld (0D1BCh),a
  call BOXFILL
  ld de,SELTXT
  ld hl,0B0Eh
  call PRINTS
  ld hl,0B11h
  call PRINTS
  ld hl,0B13h
  call PRINTS
sl_w:
  call WAITKEY
  cp 31h
  ret z
  cp 32h
  jr nz,sl_w
  call SWAPCH
  ; nombres: izquierda <- F. ROMAY ; derecha <- nombre del campo izquierdo
  ld hl,9453h
  ld de,ITUNAME
  ld bc,10
  ldir
  ld hl,945Fh
  ld de,9453h
  ld bc,10
  ldir
  ld hl,ITUNAME
  ld de,945Fh
  ld bc,10
  ldir
  ld a,1
  ld (NSW),a
  ret
"""

R_MENU = """
; ---- A095h: entrada al menu: volver al estado normal ----
MENUH:
{MENU_EXTRA}
  ld a,(SWAPPED)
  or a
  call nz,SWAPCH
  ld a,(NSW)
  or a
  jr z,mh_e
  xor a
  ld (NSW),a
  ld hl,ITUNAME
  ld de,9453h
  ld bc,10
  ldir
mh_e:
  jp 0A5FDh
SELTXT:
  db 'JUGADOR 1',0FFh,'1 - ITU',0FFh,'2 - ROMAY',0FFh
"""

MSX2 = False          # en la ROM MSX2 el menu restaura sus graficos (los planos de sprites usan E740h-F27Fh)
INIT_ADDR = 0
MENUX_ADDR = 0
def place():
    extra = ('  call %d' % MENUX_ADDR) if MSX2 else ''
    return [R_MIR + R_MCPY, R_SEL + R_MENU.replace('{MENU_EXTRA}', extra) + R_SWAP]


def asm_str(src):
    # convertir 'texto' en bytes para el ensamblador
    def rep(m):
        return ','.join(str(ord(ch)) for ch in m.group(1))
    return re.sub(r"'([^']*)'", rep, src)


def build(place_=None):
    place_ = place_ or place()
    blocks = list(zip(FRAGS, place_))
    names = [set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', s, re.M)) for _, s in blocks]
    labs = [{n: 0 for n in ns} for ns in names]
    for _ in range(6):
        out = []; new = []
        for k, ((org, lim), src) in enumerate(blocks):
            consts = {}
            for j, l in enumerate(labs):
                if j != k: consts.update(l)
            code, L, a = assemble(COMMON + asm_str(src), org, consts)
            out.append(code); new.append({n: v for n, v in L.items() if n in names[k]})
        if new == labs: break
        labs = new
    for (org, lim), code in zip(FRAGS, out):
        assert org + len(code) <= lim, ('hueco lleno', hex(org), len(code), lim - org)
    L = {}
    for l in labs: L.update(l)
    return out, L


def init_code(chunks):
    """rutina de arranque en el area de preparacion: copia los trozos, limpia banderas,
    se desengancha y salta a A0A1h"""
    src = ""
    off = 0x40
    for (org, lim), code in zip(FRAGS, chunks):
        src += f"  ld hl,{STAGE + off}\n  ld de,{org}\n  ld bc,{len(code)}\n  ldir\n"
        off += len(code)
    src += f"""
  xor a
  ld ({SWAPPED}),a
  ld ({NSW}),a
  ld hl,0A0A1h
  ld (84E9h),hl
  jp 0A0A1h
"""
    code, _, _ = assemble(src, STAGE)
    assert len(code) <= 0x40
    return code


def stage_bytes():
    chunks, L = build()
    blob = bytearray(init_code(chunks).ljust(0x40, b'\0'))
    for c in chunks: blob += c
    return bytes(blob), L


def apply(F1, F2, F3):
    blob, L = stage_bytes()
    w = lambda v: [v & 255, v >> 8]
    def p3(at, old, new):
        i = at - 0x84D0
        assert bytes(F3[i:i + len(old)]) == bytes(old), (hex(at), bytes(F3[i:i + len(old)]).hex())
        F3[i:i + len(new)] = bytes(new)
    p3(0x84E8, [0xCD, 0xA1, 0xA0], [0xCD] + w(STAGE))
    p3(0xA095, [0xC3, 0xFD, 0xA5], [0xC3] + w(L['MENUH']))
    p3(0xA6C7, [0x3E, 0x01, 0x32, 0x06, 0xB2], [0xCD] + w(L['SELH']) + [0, 0])
    # comprobar que los bytes conmutables son los esperados
    for a, x in TOGGLES:
        if a >= 0xB3B0:
            assert F1[a - 0xB3B0] in (0x0B,), hex(a)
        else:
            assert F3[a - 0x84D0] in (0x38, 0x30), hex(a)


def ext_patch(ext):
    """escribe el blob en la extension del fichero 1 (DD19h..E73Fh)"""
    blob, _ = stage_bytes()
    o = STAGE - 0xDD19
    assert all(b == 0 for b in ext[o:o + len(blob)])
    ext[o:o + len(blob)] = blob
    return ext


if __name__ == '__main__':
    chunks, L = build()
    for (org, lim), c in zip(FRAGS, chunks): print('%04X: %d/%d bytes' % (org, len(c), lim - org))
    print({k: '%04X' % v for k, v in L.items() if k.isupper()})
