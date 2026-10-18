"""Nueva disposicion de la pantalla del partido (CPC): pista y canastas 18 lineas mas abajo, publico y
valla 13 lineas mas arriba, banda gris de tres escalones entre la valla y la pista, publico fuera del
bufer y marcador compacto."""
import numpy as np
import smallfont
DY = 18                     # la pista baja 18 lineas
BUF0 = 24 + DY              # linea de pantalla de la fila 0 del bufer (42)
BLUE, BLACK, WHITE, PINK = 0, 1, 2, 3
LCD = ['3c66662466663c00', '0406060406060400', '3c06063c60603c00', '3c06063c06063c00', '2466663c06060400',
       '3c60603c06063c00', '3c60603c66663c00', '3c06060406060400', '3c66663c66663c00', '3c66663c06063c00']

LIFT = 13                   # el publico y la valla suben 13 lineas: el publico (11-41) queda fuera del bufer
CROWD0 = 24 - LIFT          # primera linea del publico (11)
BB0 = 55 - LIFT             # primera linea de la valla (42 = fila 0 del bufer)

def band_edge(y):           # borde izquierdo de la banda (x del primer pixel); fijo desde la linea 84
    return 56 if y >= 84 else 59 - (y - 60) * 3 // 24

def band_stripe(y):         # franjas de tramado (escalones) de la banda, lineas 60-97
    return 61 <= y <= 72 or 74 <= y <= 96

def build_static(S):
    """S: pantalla estatica antigua (200x320 tintas). Devuelve la nueva."""
    N = np.full((200, 320), BLACK, np.uint8)
    # publico (antes 24-54) y valla (55-72), 13 lineas mas arriba, sin las canastas
    N[CROWD0:CROWD0 + 49] = S[24:73]
    N[CROWD0:CROWD0 + 49, 0:56] = BLACK; N[CROWD0:CROWD0 + 49, 266:320] = BLACK
    # banda: tres escalones de tramado entre la valla (acaba en 59) y la pista (98)
    for y in range(60, 98):
        xl = band_edge(y); xr = 319 - xl
        for x in range(xl, xr + 1):
            if x in (xl, xr): N[y, x] = WHITE
            elif band_stripe(y): N[y, x] = WHITE if (x + y) % 2 == 0 else BLACK
    xl = band_edge(60); N[59, xl:320 - xl] = WHITE
    bench(N); palco(N); jug(N); sitter(N)
    # canastas (tableros) 18 lineas mas abajo
    for x0, x1 in ((28, 56), (266, 292)):
        N[16 + DY:66 + DY, x0:x1] = S[16:66, x0:x1]
    # pista
    N[80 + DY:128 + DY] = S[80:128]
    return N

# banco de suplentes de madera (izquierda; el derecho en espejo). Lineas 68-85 y sombra en 86-87: lo que pasa de la 87
# costaria memoria (las filas 88-97 de la banda son todas iguales y se guardan una sola vez)
BENCH = [
    "################################################################",
    "#WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW#",
    "#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS#",
    "#SSSSSS###SSSSSSSSSSSSSSSS##SSSSSSSSSSSSSSSS###SSSSSSSSSSSSSSSS#",
    "#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS#",
    "################################################################",
    "  #SS#              #SS#              #SS#               #SS#   ",
    "  #SS#              #SS#              #SS#               #SS#   ",
    "################################################################",
    "#WSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWSWS#",
    "#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS#",
    "#SSSSSSSSSSSSS##SSSSSSSSSSSSSSSSS##SSSSSSSSSSSSSSSSS##SSSSSSSSS#",
    "#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS#",
    "#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S##",
    "################################################################",
    "  #SS#              #SS#              #SS#               #SS#   ",
    "  #SS#              #SS#              #SS#               #SS#   ",
    "  #WW#              #WW#              #WW#               #WW#   ",
]
BENCH_Y, BENCH_X = 68, 64
def bench(N):
    # sombra negra de dos lineas bajo el banco (lineas 86-87)
    y = BENCH_Y + len(BENCH)
    N[y:y + 2, BENCH_X + 2:BENCH_X + len(BENCH[0]) + 2] = BLACK
    N[y:y + 2, 319 - (BENCH_X + len(BENCH[0]) + 1):319 - (BENCH_X + 1)] = BLACK
    for dy, row in enumerate(BENCH):
        for dx, c in enumerate(row):
            if c == ' ': continue
            pen = {'#': BLACK, 'S': PINK, 'W': WHITE}[c]
            N[BENCH_Y + dy, BENCH_X + dx] = pen
            N[BENCH_Y + dy, 319 - (BENCH_X + dx)] = pen

# botijo junto al banco de la izquierda (lineas 73-87)
JUG = [
    "    ##      ",
    "   #WS#  #  ",
    "    #S# #S# ",
    "   #SSS#S#  ",
    "  #SSSSSS#  ",
    " #SWSSSSSS# ",
    " #WSSSSSSS# ",
    "#SWSSSSSSSS#",
    "#SSSSSSSSSS#",
    "#SSSSSSSSSS#",
    "#SSSSSSSSS##",
    " #SSSSSSSS# ",
    " #SSSSSSSS# ",
    "  ##SSSS##  ",
    "    ####    ",
]
def sprite(N, rows, x0, y0, transp=' '):
    for dy, row in enumerate(rows):
        for dx, c in enumerate(row):
            if c != transp: N[y0 + dy, x0 + dx] = {'#': BLACK, 'S': PINK, 'W': WHITE, '.': BLUE}[c]
def jug(N): sprite(N, JUG, 122, 88 - len(JUG))

# Fernando Martin (el jugador de la derecha del original) sentado en el banco de la derecha:
# cabeza de frente (fotograma 22h) sobre el cuerpo de frente (19h), sin muslos (van hacia nosotros)
SIT_HEAD = [   # filas 3-15 de 22h (la cabeza de frente de F. Martin)
    "...###..#...",
    "..#####W##..",
    "..#####W##..",
    "..##S##W##..",
    ".###SSSSS##.",
    ".#SS##S####.",
    ".#SSS#S#SS#.",
    ".#SSSSSSS##.",
    "..#S####S#..",
    "..#SSSSSS#..",
    "..#SSSSSS#..",
    "...#SSSS#...",
    "....####....",
]
SIT_BODY = [   # filas 5-17 y 24-30 de 19h
    "...####SSSSSS####.......",
    "..#SS#W#SSSS#W#SS#......",
    ".#SSS#WW#SS#WW#SSS#.....",
    ".#SS##WWW##WWW##SS#.....",
    "#SS#.#WWWWWWWW#.#SS#....",
    "#SS#..#WWWWWW#..#SS#....",
    "#SS#..#WWWWWW#..#SS#....",
    ".#SS#.#WWWWWW#.#SS#.....",
    ".#SS#..#WWW##..#SS#.....",
    ".#S#..#W###WW#..#S#.....",
    "..##..#WWWWWW#..##......",
    ".....#WWWW#WWW#.........",
    ".....#WWWW#WWW#.........",
    "....#WW#....#WW#........",
    ".....#WW#..#WW#.........",
    ".....####..####.........",
    "....#####..#####........",
    "...##WW##..##WW##.......",
    "...#WWWW#..#WWWW#.......",
    "....####....####........",
]
SIT_X = 216
def sitter(N):
    yb = 88 - len(SIT_BODY)
    sprite(N, SIT_BODY, SIT_X, yb, '.')
    sprite(N, SIT_HEAD, SIT_X + 4, yb - len(SIT_HEAD) + 1, '.')

# palco VIP en el centro (ventana azul para el invitado y cartel DUCADOS), lineas 61-85
def palco(N):
    import smallfont
    x0, x1 = 136, 183
    N[61:86, x0:x1 + 1] = BLACK
    N[61, x0:x1 + 1] = WHITE; N[61:86, x0] = WHITE; N[61:86, x1] = WHITE
    N[62:73, x0 + 2:x1 - 1] = BLUE                 # interior del palco
    N[73, x0:x1 + 1] = WHITE                          # baranda
    N[74, x0 + 1:x1] = BLACK
    N[75:85, x0 + 2:x1 - 1] = BLUE                 # cartel
    N[85, x0:x1 + 1] = WHITE
    for y in (75, 84): N[y, x0 + 2:x1 - 1] = WHITE
    smallfont.render(N, x0 + 3, 76, 'DUCADOS', WHITE, bg=BLUE)
    # el invitado: Alan Sugar (pelo rizado, barba, traje y corbata negros, camisa blanca)
    for dy, row in enumerate(VIP):
        for dx, c in enumerate(row):
            if c != '.': N[62 + dy, 149 + dx] = {'#': BLACK, 'S': PINK, 'W': WHITE}[c]

VIP = [
    ".....##.##.##.##.....",
    "....##############...",
    "...################..",
    "...####SSSSSSSS####..",
    "...###SS#SSSS#SS###..",
    "....##SSSSSSSSSS##...",
    "....##SS######SS##...",
    ".....##S#SSSS#S##....",
    "......##########.....",
    "....####WWW#WWW####..",
    "..#######WW#WW#######",
]

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
