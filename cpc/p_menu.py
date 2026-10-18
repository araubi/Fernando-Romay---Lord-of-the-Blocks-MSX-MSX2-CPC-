"""Menu: (C) NIDAMIC en la cadena del copyright (ya no se imprime: el rotulo del menu lo lleva, ver p_menubg)."""
def apply(im):
    im.poke(0x23AC, b'NIDAMIC', b'DINAMIC')
