import pickle, bisect
m2c, c2m, mp = pickle.load(open('../out/maps.pkl', 'rb'))
inv = {v: k for k, v in mp.items()}
ms = sorted(inv)
def m2cpc(a, verbose=False):
    if a in inv: return inv[a], 'code'
    if a in m2c: return m2c[a], 'op'
    i = bisect.bisect_right(ms, a) - 1
    if i >= 0 and a - ms[i] < 32:
        b = ms[i]; return inv[b] + (a - b), 'near+%d' % (a - b)
    return None, None
if __name__ == '__main__':
    import sys
    for s in sys.argv[1:]:
        v = int(s, 16); r, k = m2cpc(v); print(s, '->', ('%04X' % r) if r is not None else None, k)
