import pickle
def cpc_frames(r, tab=0x66F4, base=0x32C8, n=None):
    out = {}
    i = 0
    while True:
        p = r[tab + 2 * i] | r[tab + 2 * i + 1] << 8
        if n is not None and i >= n: break
        e = base + p; h = r[e]; w = r[e + 1]
        if n is None and (w != 6 or h == 0 or h > 64): break
        rows = []
        for y in range(h):
            row = r[e + 2 + w * y:e + 2 + w * y + w]; s = []
            for b in row:
                for k in range(4): s.append(((b >> (7 - k)) & 1) | (((b >> (3 - k)) & 1) << 1))
            rows.append(s)
        out[i] = (e, rows); i += 1
    return out
def msx_frames(r, tab=0x7760, base=0x415A, n=None):
    out = {}; i = 0
    while True:
        if n is not None and i >= n: break
        p = r[tab + 2 * i] | r[tab + 2 * i + 1] << 8
        e = base + p; h = r[e]; w = r[e + 1]
        if n is None and (w != 6 or h == 0 or h > 64): break
        rows = []
        for y in range(h):
            row = r[e + 2 + w * y:e + 2 + w * y + w]; s = ''
            hw = w // 2
            for x in range(hw * 8):
                d = row[x // 8] & (0x80 >> (x % 8)); mk = row[hw + x // 8] & (0x80 >> (x % 8))
                s += '#' if d else ('.' if mk else 'o')
            rows.append(s)
        out[i] = (e, rows); i += 1
    return out
