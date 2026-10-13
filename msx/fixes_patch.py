"""- Barra de energia (fallo del original): las dos escrituras a VRAM de cada bloque (9F59h/9F5Ch)
  iban separadas solo 22 ciclos (ADD HL,HL) y el TMS9918 necesita >= 29 durante la imagen activa:
  la segunda fila del bloque a veces se perdia. Se cambia por EX (SP),HL (19 ciclos; en la pila
  esta el mismo HL, asi que no altera nada).
- Modo 2 jugadores: nombre por defecto del campo derecho "F. ROMAY" en lugar de "JUGADOR 2"."""
def apply(F1,F2,F3):
    i=0x9F59-0x84D0
    assert bytes(F3[i:i+7])==bytes([0xD3,0x98,0x29,0xD3,0x98,0xE1,0xC9])
    F3[i+2]=0xE3
    i=0xA7FD-0x84D0
    assert bytes(F3[i:i+10])==b'JUGADOR 2 ', bytes(F3[i:i+10])
    F3[i:i+10]=b'F. ROMAY  '
