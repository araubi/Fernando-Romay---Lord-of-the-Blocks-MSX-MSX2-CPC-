"""Colores por zonas durante el partido (como el MSX2): la tinta 0 (fondo) cambia a mitad de pantalla.
Arriba (publico y valla) azul, la pista color parque (naranja) y el marcador otra vez azul.
Se usan las interrupciones del gate array (cada 52 lineas): con R7=31 (la imagen sube 8 lineas
respecto al VSYNC) caen en y=94 (en la banda gris, antes de la pista que empieza en y=98) y en
y=146 (entre la pista, que acaba en y=145, y el marcador, que empieza en y=147).
En la repeticion ampliada la pista empieza en y=112 y y=94 cae en la banda ampliada; cuando la imagen
ampliada ya pasa de y=146 (MATCH=2) la pista sigue naranja hasta abajo.
Fuera del partido (menu y estadisticas, LEAVE) se vuelve a R7=30 y a la tabla de volcado original.
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
  ld a,(8118h)
  cp 98h
  ld a,42
  call nz,SETTAB
  ld bc,0BC07h
  out (c),c
  ld bc,0BD00h + 31
  out (c),c
  jp 8348h
; fundido a negro (7588h): desactiva (el fundido pone todas las tintas, la 0 incluida)
MOFF:
  xor a
  ld (MATCH),a
  ld a,2
  ld (7394h),a          ; FULLF de p_partial: tras el fundido, copia y volcado completos
  ret
@@SPLIT@@
; fuera del partido (menu y estadisticas): R7=30 y tabla de volcado original
LEAVE:
  ld bc,0BC07h
  out (c),c
  ld bc,0BD00h + 30
  out (c),c
  ld a,24
; tabla de lineas del volcado (8118h): fila 0 del bufer en la linea A
SETTAB:
  ld l,a
  ld h,0
  add hl,hl
  ld de,7B70h
  add hl,de
  ld de,8118h
  ld b,104
st_1:
  ld a,(hl)
  add a,8
  ld (de),a
  inc hl
  inc de
  ld a,(hl)
  adc a,0
  ld (de),a
  inc hl
  inc de
  djnz st_1
  ret
@@SPLIT@@
BLACKH:
  call MOFF
  xor a
  ld (75F0h),a
  ret
; 2502h: fin de cada fila de la imagen ampliada. Cuando ya pasa de y=146 (fila 73 de 100) solo queda
; el marcador antiguo por debajo: a partir de ahi la pista sigue naranja hasta abajo (MATCH=2)
ZROW:
  ld b,a
  cp 27
  jr nz,zr_1
  ld a,2
  ld (MATCH),a
zr_1:
  ld de,0018h
  ret
@@SPLIT@@
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
