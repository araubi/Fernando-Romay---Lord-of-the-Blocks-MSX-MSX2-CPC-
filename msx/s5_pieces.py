"""Piezas (sprites software) del juego: tabla 7760h (pagina 1, cargada desde F2 8534h->415Ah)."""
from common import cas_blocks
def files_of(cas):
    _, segs = cas_blocks(cas); out = {}
    for n, ci in (('f1', 3), ('f2', 5), ('f3', 7)):
        c = segs[ci]; s = c[0] | c[1] << 8; e = c[2] | c[3] << 8; x = c[4] | c[5] << 8
        out[n] = (s, e, x, bytes(c[6:6 + e - s + 1]))
    return out
class Pieces:
    def __init__(s, cas):
        F = files_of(cas); s.F = F
        s2, e2, x2, f2 = F['f2']; s.f2 = f2
    def p1(s, a): return s.f2[a - 0x415A + (0x8534 - 0x8534)]
    def entry(s, i):
        a = 0x7760 + 2 * i; return 0x415A + (s.p1(a) | s.p1(a + 1) << 8)
    def piece(s, i):
        """-> (h, wbytes, rows) ; rows[y] = (data bytes, mask bytes) ; ancho en px = wbytes*4"""
        a = s.entry(i); h = s.p1(a); w = s.p1(a + 1); a += 2; rows = []
        nb = w // 2
        for y in range(h):
            b = [s.p1(a + k) for k in range(w)]; a += w
            rows.append((b[:nb], b[nb:]))
        return h, w, rows
    def chars(s, i):
        """'#' tinta, 'o' interior (mascara 0), '.' transparente"""
        h, w, rows = s.piece(i); out = []
        for d, m in rows:
            line = ''
            for bx in range(len(d)):
                for k in range(8):
                    bit = 0x80 >> k
                    line += '#' if d[bx] & bit else ('o' if not m[bx] & bit else '.')
            out.append(line)
        return out
