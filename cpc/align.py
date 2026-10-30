import pickle, re, dz80, disall, collections
def norm(t): return re.sub(r'[0-9A-F]{4}h', 'N', t)
def seqs(mem, code, K=6):
    addrs = sorted(code); idx = {a: i for i, a in enumerate(addrs)}
    S = {}
    for i, a in enumerate(addrs):
        win = []; b = a
        for k in range(K):
            if b not in code: break
            t, l = code[b]; win.append(norm(t)); b += l
        if len(win) == K: S[a] = tuple(win)
    return S
cm, cc = pickle.load(open('../out/cpc_game1.pkl', 'rb'))
cmem = bytearray(cm.ram); ccov = pickle.load(open('../out/cov1.pkl', 'rb'))
ccode, _ = disall.trace(cmem, [p for p in ccov if 0x100 <= p < 0xC000])
mmem = bytearray(open('../out/msx_ram.bin', 'rb').read()); mcov = pickle.load(open('../out/msx_cov.pkl', 'rb'))
mcode, _ = disall.trace(mmem, [p for p in mcov if 0x8000 <= p < 0xF380], 0x8000, 0xF380)
K = 6
CS = seqs(cmem, ccode, K); MS = seqs(mmem, mcode, K)
mi = collections.defaultdict(list)
for a, s in MS.items(): mi[s].append(a)
ci = collections.defaultdict(list)
for a, s in CS.items(): ci[s].append(a)
mp = {}
for a, s in CS.items():
    if len(mi.get(s, [])) == 1 and len(ci[s]) == 1: mp[a] = mi[s][0]
# extender: propagar instruccion a instruccion
changed = True
while changed:
    changed = False
    for a in sorted(mp):
        b = mp[a]
        if a in ccode and b in mcode:
            na = a + ccode[a][1]; nb = b + mcode[b][1]
            if na in ccode and nb in mcode and na not in mp and norm(ccode[na][0]) == norm(mcode[nb][0]):
                mp[na] = nb; changed = True
print('cpc code', len(ccode), 'msx code', len(mcode), 'mapped', len(mp))
pickle.dump((mp, ccode, mcode), open('../out/align.pkl', 'wb'))
# segmentos contiguos
segs = []; prev = None
for a in sorted(mp):
    d = mp[a] - a
    if segs and segs[-1][2] == d and a - segs[-1][1] < 64: segs[-1][1] = a
    else: segs.append([a, a, d])
for s0, s1, d in segs:
    if s1 - s0 > 20: print('%04X-%04X -> %04X-%04X' % (s0, s1, s0 + d, s1 + d))
