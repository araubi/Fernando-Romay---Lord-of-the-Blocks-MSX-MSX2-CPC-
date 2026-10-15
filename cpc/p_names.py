"""Nombres: ITURRIAGA (campo izquierdo) y F. ROMAY (derecho, tambien por defecto en 2 jugadores)."""
def apply(im):
    im.poke(0x1176, b' ITURRIAGA ', b'JUGADOR  1 ')
    im.poke(0x1182, b' F. ROMAY  ', b' MARTIN F. ')
    im.poke(0x23DB, b' F. ROMAY  ', b' MARTIN F. ')
    im.poke(0x23E7, b' F. ROMAY  ', b' JUGADOR 2 ')
