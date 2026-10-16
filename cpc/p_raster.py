"""Colores por zonas durante el partido (como el MSX2): la tinta 0 (fondo) cambia a mitad de pantalla.
Arriba (publico y valla) azul, la pista color parque (naranja) y el marcador otra vez azul.
Se usan las interrupciones del gate array (cada 52 lineas): con R7=29 (la imagen baja 8 lineas
respecto al VSYNC) caen en y=78 (en la franja de cuadros, antes de la pista que empieza en y=80) y en
y=130 (entre la pista, que acaba en y=127, y el marcador, que empieza en y=136).
En la repeticion ampliada (MATCH=2) la pista empieza en y=112: se espera desde y=78 hasta ~y=104.
El manejador de interrupcion del juego (7511h) cuenta las interrupciones desde el VSYNC.
No se toca nada mientras la paleta esta en negro (fundidos: la tinta 0 de la tabla 73B2h no es 15h)."""
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
  ld a,(73B2h)
  cp 15h
  jp nz,751Bh
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
  ld a,(73B2h)
  cp 15h
  jp nz,7533h
  ld a,c
  cp 3
  jp z,ra_c
  cp 4
  jp nz,7533h
  ld a,(MATCH)
  cp 2
  jp z,7533h
  ld a,{TOP}
  jp ra_s
@@SPLIT@@
ra_c:
  ld a,(MATCH)
  cp 2
  call z,ZWAIT
  ld a,{COURT}
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
; fundido a negro (7588h): desactiva (el fundido pone todas las tintas, la 0 incluida)
MOFF:
  xor a
  ld (MATCH),a
  ret
@@SPLIT@@
BLACKH:
  call MOFF
  xor a
  ld (75F0h),a
  ret
; 2502h: fin de cada fila de la imagen ampliada. Cuando ya va por y=104 (fila 52 de 100) la parte
; de arriba es la imagen ampliada y la de abajo la pista normal: a partir de ahi, colores de la repeticion
ZROW:
  ld b,a
  cp 48
  jr nz,zr_1
  ld a,2
  ld (MATCH),a
zr_1:
  ld de,0018h
  ret
@@SPLIT@@
; repeticion ampliada: la pista empieza en y=112 (franja de cuadros y=98-111); la interrupcion
; llega en y=78: se esperan unas 26 lineas
ZWAIT:
  ld bc,238
zw_1:
  dec bc
  ld a,b
  or c
  jr nz,zw_1
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
    im.poke(0x2502, [0xCD] + w(L['ZROW']) + [0], [0x47, 0x11, 0x18, 0x00])
    # al redibujar la pantalla del partido (tras canasta/descanso) ya con los colores del partido
    im.poke(0x101F, [0xCD] + w(L['MLOOP']), [0xCD, 0x48, 0x83])
