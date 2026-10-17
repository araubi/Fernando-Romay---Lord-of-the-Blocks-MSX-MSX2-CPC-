"""Fondo del partido con la nueva disposicion (ver p_layout y design), empaquetado: las filas repetidas
(los escalones de la banda) se guardan una sola vez y una tabla de filas (BGTAB) da la direccion de
cada fila. El fondo lo leen solo 8348h y la reposicion del volcado parcial (p_partial), por la tabla.
La memoria que sobra al final del fondo queda libre."""
import bg, design
from p_layout import old_static, BG
from p_partial import BGTAB


def apply(im):
    S = old_static(im)
    im.oldS = S
    N = design.build_static(S)
    C0 = design.CROWD0
    N[C0:C0 + 31, 32 + 4 * 32:32 + 4 * 53] = N[C0:C0 + 31, 32 + 4 * 11:32 + 4 * 32]
    # fondo nuevo empaquetado: las filas repetidas (banda) una sola vez; tabla de filas en BGTAB
    rows = [bg.encode(N[42 + r:43 + r, 32:288]) for r in range(104)]
    assert b''.join(rows[56:]) == im.rd(BG + 56 * 64, 48 * 64), 'la pista deberia ser la misma'
    uniq = []; tab = []
    for rw in rows:
        if rw not in uniq: uniq.append(rw)
        tab.append(BG + 64 * uniq.index(rw))
    assert BG + 64 * len(uniq) <= BGTAB, len(uniq)
    im.poke(BG, b''.join(uniq))
    im.poke(BGTAB, b''.join(bytes([a & 255, a >> 8]) for a in tab))
    im.free.append([BG + 64 * len(uniq), BGTAB])
    im.free.append([BGTAB + 208, 0xA568])
