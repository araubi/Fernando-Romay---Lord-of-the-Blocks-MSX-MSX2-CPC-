"""Colores por zonas durante el partido (como el MSX2): la tinta 0 (fondo) cambia a mitad de pantalla.
Arriba (publico y valla) azul, la pista color parque (naranja) y el marcador otra vez azul.
Se usan las interrupciones del gate array (cada 52 lineas): con R7=29 (la imagen baja 8 lineas
respecto al VSYNC) caen en y=78 (en la franja de cuadros, antes de la pista que empieza en y=80) y en
y=130 (entre la pista, que acaba en y=127, y el marcador, que empieza en y=136).
El manejador de interrupcion del juego (7511h) cuenta las interrupciones desde el VSYNC."""
COURT = 0x0E | 0x40      # naranja
TOP = 0x15 | 0x40        # azul brillante (el del juego)
SRC = """
RASTER:
  push bc
  push af
  ld b,0F5h
  in a,(c)
  rra
  jp nc,ra_n
  xor a
  ld (RCNT),a
  ld a,(MATCH)
  or a
  jp z,751Bh
  ld bc,7F00h
  out (c),c
  ld a,{TOP}
  out (c),a
  jp 751Bh
@@SPLIT@@
ra_n:
  ld a,(RCNT)
  inc a
  ld (RCNT),a
  ld c,a
  ld a,(MATCH)
  or a
  jp z,7533h
  ld a,c
  cp 3
  ld a,{COURT}
  jr z,ra_s
  ld a,c
  cp 4
  jp nz,7533h
  ld a,{TOP}
ra_s:
  ld bc,7F00h
  out (c),c
  out (c),a
  jp 7533h
@@SPLIT@@
; bucle del partido (02A3h): activa
MLOOP:
  ld a,1
  ld (MATCH),a
  ld bc,0BC07h
  out (c),c
  ld bc,0BD00h + 29
  out (c),c
  jp 8348h
; fundido a negro (7588h) y zoom (2417h): desactiva y deja el azul
MOFF:
  xor a
  ld (MATCH),a
  ld bc,7F00h
  out (c),c
  ld a,{TOP}
  out (c),a
  ret
@@SPLIT@@
BLACKH:
  call MOFF
  xor a
  ld (75F0h),a
  ret
ZOOMH:
  call MOFF
  ld hl,6792h
  ret
MATCH: db 0
RCNT: db 0
"""
def apply(im):
    src = SRC.replace('{TOP}', str(TOP)).replace('{COURT}', str(COURT))
    L = im.place_many('raster', src.split('@@SPLIT@@'))
    w = lambda v: [v & 255, v >> 8]
    im.poke(0x7511, [0xC3] + w(L['RASTER']), [0xF3, 0xC5, 0xF5])
    im.poke(0x02A3, [0xCD] + w(L['MLOOP']), [0xCD, 0x48, 0x83])
    im.poke(0x7588, [0xCD] + w(L['BLACKH']) + [0], [0xAF, 0x32, 0xF0, 0x75])
    im.poke(0x2417, [0xCD] + w(L['ZOOMH']), [0x21, 0x92, 0x67])
