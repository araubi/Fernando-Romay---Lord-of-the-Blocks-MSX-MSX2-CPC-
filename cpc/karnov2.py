"""Karnov (forzudo calvo, con bigote y sin camiseta) en la grada, en el publico normal y en el animado."""
import numpy as np
STATIC = [
"......######......",
".....#pppppp#.....",
"....#pppppppp#....",
"....#p##pp##p#....",
"....#pppppppp#....",
"....#p######p#....",
".....#pp##pp#.....",
"......#pppp#......",
"..#####pppp#####..",
".#pppppppppppppp#.",
"#pppp##pppp##pppp#",
"#pppppppppppppppp#",
"#ppppppp##ppppppp#",
"#pppppppppppppppp#",
"#pppppppppppppppp#",
]
CHEER = [
"#p#...######...#p#",
"#p#..#pppppp#..#p#",
"#p#.#pppppppp#.#p#",
"#p#.#p##pp##p#.#p#",
"#p#.#pppppppp#.#p#",
"#pp##p######p##pp#",
".#pp#p#wwww#p#pp#.",
"..#pp#p####p#pp#..",
"...#pp#pppp#pp#...",
"...#pppppppppp#...",
"..#pppp#pp#pppp#..",
"..#pppppppppppp#..",
"..#pppppp#ppppp#..",
".#pppppppppppppp#.",
".#pppppppppppppp#.",
]
C = {'#': 1, 'p': 3, 'w': 2}
def paste(a, spr, x0, y0):
    for y, row in enumerate(spr):
        for x, ch in enumerate(row):
            if ch != '.' and 0 <= y0 + y < a.shape[0]: a[y0 + y, x0 + x] = C[ch]
    return a
