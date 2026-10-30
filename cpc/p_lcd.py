"""Marcador con cifras LCD de 7 segmentos (las del MSX2): puntos, personales y tiempo.
Solo durante el partido (filas de texto 17-22)."""
DIG = ['3c66662466663c00', '0406060406060400', '3c06063c60603c00', '3c06063c06063c00', '2466663c06060400',
       '3c60603c06063c00', '3c60603c66663c00', '3c06060406060400', '3c66663c66663c00', '3c66663c06063c00']
SRC = """
FONTSEL:
  ld hl,(73ABh)
  ld a,(LCDON)
  or a
  ret z
  ld a,(0060h)
  cp 17
  ret c
  cp 23
  ret nc
  ld a,d
  cp 1
  ret nz
  ld a,e
  cp 80h
  ret c
  cp 0D0h
  ret nc
  ld hl,LCDF-180h
  ret
LCDON: db 0
LCDF:
""" + '\n'.join('  db ' + ','.join(str(b) for b in bytes.fromhex(h)) for h in DIG) + "\n"
def apply(im):
    L = im.place('lcd', SRC)
    im.poke(0x79EE, [0xCD, L['FONTSEL'] & 255, L['FONTSEL'] >> 8], [0x2A, 0xAB, 0x73])
