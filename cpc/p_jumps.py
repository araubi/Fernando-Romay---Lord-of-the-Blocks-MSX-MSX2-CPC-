"""Saltos, tiros y mates (piezas 30h-3Dh) con los retoques del MSX1 final (barba de Itu, pelo y
nariz de Romay...). Se aplican solo los pixeles cambiados, desplazados como en la version CPC; los
pixeles de relleno nuevos toman el color (blanco/piel) del vecindario."""
import frames
from p_heads import pack, entry
IDX = list(range(0x30, 0x3E))
SHIFT = {0x33: 4, 0x34: 4}
def build_frames(cpc_mem):
    Mo = frames.msx_frames(open('/home/claude/cpc/msx_ram.bin', 'rb').read(), n=75)
    Mf = frames.msx_frames(open('/home/claude/cpc/msxfin_ram.bin', 'rb').read(), n=75)
    C = frames.cpc_frames(cpc_mem, n=75)
    out = {}
    for i in IDX:
        d = SHIFT.get(i, 0)
        co = C[i][1]; mo = Mo[i][1]; mf = Mf[i][1]
        H = len(co); W = len(co[0])
        new = [list(r) for r in co]
        pend = []
        for y in range(H):
            for x in range(24):
                if mo[y][x] == mf[y][x]: continue
                X = x + d
                if not 0 <= X < W: continue
                ch = mf[y][x]
                if ch == '#': new[y][X] = 1
                elif ch == '.': new[y][X] = 0
                else:
                    if co[y][X] in (2, 3): new[y][X] = co[y][X]
                    else: new[y][X] = -1; pend.append((X, y))
        for it in range(6):
            left = []
            for X, y in pend:
                cnt = {2: 0, 3: 0}
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, X + dx
                        if 0 <= yy < H and 0 <= xx < W and new[yy][xx] in (2, 3): cnt[new[yy][xx]] += 1
                if cnt[2] + cnt[3]: new[y][X] = 3 if cnt[3] >= cnt[2] else 2
                else: left.append((X, y))
            pend = left
        for X, y in pend: new[y][X] = 3
        out[i] = new
    return out
def apply(im):
    m = im.mem()
    F = build_frames(bytes(m))
    for i, rows in F.items():
        e = entry(im, i)
        assert im.rd(e, 2) == bytes([len(rows), 6])
        im.poke(e + 2, pack(rows))
