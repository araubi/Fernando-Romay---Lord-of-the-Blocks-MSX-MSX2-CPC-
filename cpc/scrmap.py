"""Pantalla de 256x176 (CRTC R1=32, R6=22, R2=42; en la presentacion 256x192, R6=24): 64 bytes por linea
de caracteres en cada bloque de 2 KB.
Las coordenadas del juego siguen siendo las de 320x200: la columna de byte b (8-71 visibles) de la
linea y (0-199) esta en C000h + (y&7)*800h + (y>>3)*64 + b-8.
Despues de la presentacion la imagen empieza en la fila 1 (R13=32) en todas las pantallas (menu, partido,
estadisticas): se ven las lineas 8-183. Cada bloque tiene libres la fila 0 (+000h-03Fh) y desde la 23
(+5C0h-7FFh): 640 bytes, 5 KB en total.
- FREE_EARLY (+600h-7FFh): la presentacion no los usa; llegan con su pantalla comprimida.
- FREE_LATE (fila 0 y fila 23): la presentacion (256x192) los ocupa; su contenido se guarda en el
  historial de la repeticion (aun sin uso) y se copia al terminar la presentacion."""
def addr(y, b=8): return 0xC000 + (y & 7) * 0x800 + (y >> 3) * 64 + b - 8
def vaddr(y): return (addr(y, 8) - 8) & 0xFFFF     # 'columna 0' virtual (tabla 7B70h)
FREE_EARLY = [(0xC000 + k * 0x800 + 0x600, 0xC000 + k * 0x800 + 0x800) for k in range(8)]
# (sin C000h-C03Fh: la pila del juego empieza en C000h y al acabar el partido llega a desbordarse por arriba)
FREE_LATE = [r for k in range(8) for r in ((0xC000 + k * 0x800, 0xC000 + k * 0x800 + 0x40),
                                             (0xC000 + k * 0x800 + 0x5C0, 0xC000 + k * 0x800 + 0x600)) if r[0] != 0xC000]
FREE_SCR = FREE_EARLY + FREE_LATE
STASH = 0x6792      # historial de la repeticion: guarda lo de FREE_LATE hasta que acaba la presentacion
Y0, Y1 = 8, 184     # lineas visibles (despues de la presentacion)
def code_ok(pc):
    """PC valido: fuera de la pantalla visible (las zonas libres pueden tener codigo)"""
    return pc < 0xC000 or any(f0 <= pc < f1 for f0, f1 in FREE_SCR)
MENU_D = 56        # en el menu los textos, recuadros y munecos bajan 56 lineas (tabla 7B70h desplazada, TSET)
MENU_Y = 8         # el rotulo del menu empieza en la linea 8
