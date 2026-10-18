"""Pantalla de 256x192 (CRTC R1=32, R6=24, R2=42): 64 bytes por linea de caracteres en cada bloque de 2 KB.
Las coordenadas del juego siguen siendo las de 320x200: la columna de byte b (8-71 visibles) de la
linea y (0-199) esta en C000h + (y&7)*800h + (y>>3)*64 + b-8. La fila 24 (lineas 192-199) solo se ve
en el partido (la imagen empieza una fila mas abajo, R13=32). Cada bloque tiene libres sus ultimos
448 bytes (desde +640h): FREE_SCR."""
def addr(y, b=8): return 0xC000 + (y & 7) * 0x800 + (y >> 3) * 64 + b - 8
def vaddr(y): return (addr(y, 8) - 8) & 0xFFFF     # 'columna 0' virtual (tabla 7B70h)
FREE_SCR = [(0xC000 + k * 0x800 + 0x640, 0xC000 + k * 0x800 + 0x800) for k in range(8)]
def code_ok(pc):
    """PC valido: fuera de la pantalla visible (las zonas libres pueden tener codigo)"""
    return pc < 0xC000 or any(f0 <= pc < f1 for f0, f1 in FREE_SCR)
MENU_D = 48        # en el menu los textos, recuadros y munecos bajan 48 lineas (tabla 7B70h desplazada, TSET)
