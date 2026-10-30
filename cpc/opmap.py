import pickle, re, collections
mp, ccode, mcode = pickle.load(open('../out/align.pkl', 'rb'))
votes = collections.defaultdict(collections.Counter)
for a, b in mp.items():
    ta = re.findall(r'([0-9A-F]{4})h', ccode[a][0]); tb = re.findall(r'([0-9A-F]{4})h', mcode[b][0])
    for x, y in zip(ta, tb): votes[int(y, 16)][int(x, 16)] += 1
m2c = {y: c.most_common(1)[0][0] for y, c in votes.items()}
c2m = {}
for y, x in m2c.items(): c2m.setdefault(x, y)
pickle.dump((m2c, c2m, mp), open('../out/maps.pkl', 'wb'))
print(len(m2c))
if __name__ == '__main__':
    import sys
    for s in sys.argv[1:]:
        v = int(s, 16); print(s, '->', hex(m2c[v]) if v in m2c else None)
