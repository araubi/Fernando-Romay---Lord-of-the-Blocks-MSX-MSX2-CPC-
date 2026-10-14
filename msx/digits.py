"""Cifras de 7 segmentos (estilo Digital-7) para las personales y los puntos del marcador."""
FONT = [bytes.fromhex(h) for h in ('7cc6ced6e6c67c00 1838181818187e00 3c66063c60667e00 3c66061c06663c00 '
                                   '1c3c6cccfe0c1e00 7e62607c06663c00 3c66607c66663c00 7e66060c18181800 '
                                   '3c66663c66663c00 3c66663e06663c00').split()]
SEG = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg'}

def glyph(n):
    g = [[0] * 8 for _ in range(8)]
    def h(y):
        for x in range(2, 6): g[y][x] = 1
    def v(x, y0):
        ys = (y0, y0 + 1)
        if n == 1: ys = (y0 - 1, y0, y0 + 1) if y0 == 1 else (y0, y0 + 1, y0 + 2)
        for y in ys:
            g[y][x] = g[y][x + 1] = 1
    s = SEG[n]
    if 'a' in s: h(0)
    if 'g' in s: h(3)
    if 'd' in s: h(6)
    if 'f' in s: v(1, 1)
    if 'b' in s: v(5, 1)
    if 'e' in s: v(1, 4)
    if 'c' in s: v(5, 4)
    return bytes(int(''.join(map(str, r)), 2) for r in g)

DIG = [glyph(n) for n in range(10)]
# retoques del usuario (plantilla marcador_digitos_0-9 devuelta)
DIG = [bytes.fromhex(h) for h in ['3c66662466663c00', '0406060406060400', '3c06063c60603c00', '3c06063c06063c00', '2466663c06060400', '3c60603c06063c00', '3c60603c66663c00', '3c06060406060400', '3c66663c66663c00', '3c66663c06063c00']]
MAP = dict(zip(FONT, DIG))

if __name__ == '__main__':
    for n in range(10):
        print(n); print('\n'.join(format(b, '08b').replace('0', '.').replace('1', '#') for b in DIG[n]))
