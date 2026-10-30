"""Karnov (forzudo calvo, con bigote y sin camiseta) en la grada, en el publico normal y en el animado."""
import numpy as np
STATIC = [   # dibujo del usuario: cabeza calva sobre los hombros (sin cuello), bigote y perilla
".....#pppppppp#.....",
"....#pppppppppp#....",
"....#p##pppp##p#....",
"....#pppppppppp#....",
"....#p########p#....",
"....#ppp####ppp#....",
"...#ppppp##ppppp#...",
"..#pppppppppppppp#..",
".#pppppppppppppppp#.",
"#pppppppppppppppppp#",
"#pp##pppppppppp##pp#",
"#pppppppppppppppppp#",
"#pppppppp##pppppppp#",
"#pppppppppppppppppp#",
"#pppppppppppppppppp#",
]
CHEER = [    # celebrando: los brazos arriba
"#p#..#pppppppp#..#p#",
"#p#.#pppppppppp#.#p#",
"#p#.#p##pppp##p#.#p#",
"#p#.#pppppppppp#.#p#",
"#p#.#p########p#.#p#",
"#pp##ppp####ppp##pp#",
".#pp#pppp##pppp#pp#.",
"..#pppppppppppppp#..",
"..#pppppppppppppp#..",
"..#pppppppppppppp#..",
"..#p##pppppppp##p#..",
"..#pppppppppppppp#..",
"..#pppppp##pppppp#..",
"..#pppppppppppppp#..",
".#pppppppppppppppp#.",
]
C = {'#': 1, 'p': 3, 'w': 2}
def paste(a, spr, x0, y0):
    for y, row in enumerate(spr):
        for x, ch in enumerate(row):
            if ch != '.' and 0 <= y0 + y < a.shape[0]: a[y0 + y, x0 + x] = C[ch]
    return a
