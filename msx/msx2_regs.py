"""MSX2: la tabla de registros del VDP que carga LIB_INIT (D1C4h, R0..R7) pasa a SCREEN 4:
R0=04h (modo G3) y R5=3Fh (atributos de sprite en 1E00h, colores de sprite en 1C00h)."""
def apply(F1,F2,F3):
    i=0xD1C4-0xB3B0
    assert bytes(F1[i:i+8])==bytes([0x02,0xE0,0x06,0xFF,0x03,0x36,0x07,0x04]), bytes(F1[i:i+8]).hex()
    F1[i]=0x04; F1[i+5]=0x3F
