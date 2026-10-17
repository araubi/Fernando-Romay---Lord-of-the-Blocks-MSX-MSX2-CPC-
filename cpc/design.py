"""Nueva disposicion de la pantalla del partido (CPC): pista y canastas 18 lineas mas abajo,
banda gris doble entre la valla y la pista, publico fuera del bufer y marcador compacto."""
import numpy as np
import smallfont
DY = 18                     # la pista baja 18 lineas
BUF0 = 24 + DY              # linea de pantalla de la fila 0 del bufer (42)
BLUE, BLACK, WHITE, PINK = 0, 1, 2, 3
LCD = ['3c66662466663c00', '0406060406060400', '3c06063c60603c00', '3c06063c06063c00', '2466663c06060400',
       '3c60603c06063c00', '3c60603c66663c00', '3c06060406060400', '3c66663c66663c00', '3c66663c06063c00']

def band_edge(y):           # borde izquierdo de la banda (x del primer pixel de la banda)
    return int(round(59 - (y - 72) * 3.0 / 25))

def build_static(S):
    """S: pantalla estatica antigua (200x320 tintas). Devuelve la nueva."""
    N = np.full((200, 320), BLACK, np.uint8)
    # publico y valla (lineas 24-72) sin las canastas
    N[24:73] = S[24:73]
    N[24:73, 0:56] = BLACK; N[24:73, 266:320] = BLACK
    # canastas (tableros) 18 lineas mas abajo
    for x0, x1 in ((28, 56), (266, 292)):
        N[16 + DY:66 + DY, x0:x1] = S[16:66, x0:x1]
    # banda: linea blanca bajo la valla (72), dos franjas de tramado separadas por negro
    for y in range(73, 98):
        xl = band_edge(y); xr = 319 - xl
        stripe = (74 <= y <= 84) or (86 <= y <= 96)
        for x in range(xl, xr + 1):
            if x in (xl, xr): N[y, x] = WHITE
            elif stripe: N[y, x] = WHITE if (x + y) % 2 == 0 else BLACK
    # el blanco de la linea 72 hasta los bordes de la banda
    xl = band_edge(72); N[72, xl:320 - xl] = WHITE
    # pista
    N[80 + DY:128 + DY] = S[80:128]
    # tableros encima de la banda si coinciden (no deberian)
    return N

def rect(N, x0, y0, x1, y1, pen): N[y0:y1 + 1, x0:x1 + 1] = pen
def frame(N, x0, y0, x1, y1, pen):
    N[y0, x0:x1 + 1] = pen; N[y1, x0:x1 + 1] = pen; N[y0:y1 + 1, x0] = pen; N[y0:y1 + 1, x1] = pen

def panel_left(N):
    # contorno: rectangulo 32..136 x 147..180 con punta en diagonal hasta x=140
    Y0, Y1 = 147, 180
    for y in range(Y0, Y1 + 1):
        d = min(y - Y0, Y1 - y, 3)
        xr = 136 + d
        N[y, 33:xr] = BLUE
        N[y, 32] = WHITE; N[y, xr] = WHITE
    N[Y0, 32:137] = WHITE; N[Y1, 32:137] = WHITE
    # fila A: energia y personales
    rect(N, 34, 150, 86, 162, BLACK); frame(N, 35, 151, 85, 161, BLUE)
    rect(N, 88, 150, 135, 162, BLACK)
    # fila B: nombre y puntos
    rect(N, 34, 166, 105, 177, BLACK)
    rect(N, 108, 166, 135, 177, BLACK)

def center(N):
    frame(N, 141, 147, 178, 164, WHITE); rect(N, 142, 148, 177, 163, BLUE); rect(N, 144, 150, 175, 161, BLACK)
    frame(N, 148, 164, 171, 180, WHITE); rect(N, 149, 165, 170, 179, BLUE); rect(N, 151, 166, 168, 177, BLACK)

def scoreboard(N):
    N[146:184] = BLACK
    panel_left(N)
    N[146:184, 160:320] = N[146:184, 159::-1]      # panel derecho en espejo
    N[146:184, 140:180] = BLACK
    center(N)

def lcd(N, x, y, text, pen):
    for i, ch in enumerate(text):
        for dy in range(8): N[y + dy, x + 8 * i:x + 8 * i + 8] = BLACK
        if ch == ':':
            g = [0, 0x18, 0x18, 0, 0x18, 0x18, 0, 0]
        elif ch == ' ': g = [0] * 8
        else: g = bytes.fromhex(LCD[int(ch)])
        for dy in range(8):
            for dx in range(8):
                if g[dy] & (0x80 >> dx): N[y + dy, x + 8 * i + dx] = pen

def energy(N, units, right=False):
    for i in range(24):
        bar = 0 if i >= 12 else 1           # 12-23 arriba, 0-11 abajo
        k = i % 12
        y = 153 if bar == 0 else 157
        x = 36 + 4 * k
        if right: x = 319 - (x + 3)
        on = i < units
        for dy in range(2):
            for dx in range(4):
                N[y + dy, x + dx] = (WHITE if dx < 3 else BLACK) if on else BLACK
        if right and on:
            for dy in range(2): N[y + dy, x:x + 4] = [BLACK, WHITE, WHITE, WHITE]

BALL = ["##WWWW##", "#WW#WWW#", "WW#W#WWW", "W#W#WWWW", "WW#W#WWW", "#WW#WWW#", "##WW#W##", "########"]
def ball(N, x, y):
    for dy, r in enumerate(BALL):
        for dx, c in enumerate(r): N[y + dy, x + dx] = WHITE if c == 'W' else BLACK

def demo(N, nameL='ITURRIAGA', nameR='F. ROMAY', eL=24, eR=17):
    energy(N, eL); energy(N, eR, right=True)
    ball(N, 88, 152)
    lcd(N, 96, 152, '12345', WHITE); lcd(N, 184, 152, '12345', WHITE)
    lcd(N, 112, 168, '005', WHITE); lcd(N, 184, 168, '002', WHITE)
    lcd(N, 144, 152, '4:54', WHITE); lcd(N, 152, 168, '30', PINK)
    smallfont.render(N, 36, 168, (' ' + nameL).ljust(11)[:11], WHITE)
    smallfont.render(N, 218, 168, (' ' + nameR).ljust(11)[:11], PINK)
