import pickle, re, dz80, sys
def trace(mem, entries, lo=0x100, hi=0xC000):
    code = {}; todo = list(entries); refs = {}
    while todo:
        a = todo.pop()
        while lo <= a < hi and a not in code:
            t, l = dz80.dis(mem, a); code[a] = (t, l)
            nxt = a + l
            m = re.search(r'([0-9A-F]{4})h', t)
            tgt = int(m.group(1), 16) if m else None
            op = t.split()[0]
            if op in ('jp', 'jr', 'call', 'djnz') and tgt is not None:
                refs.setdefault(tgt, set()).add(a)
                if '(' not in t: todo.append(tgt)
                if op in ('jp', 'jr') and ',' not in t: break
            if t.startswith('ret') and t == 'ret': break
            if t.startswith('jp (') or t == 'reti' or t == 'retn': break
            a = nxt
    return code, refs
def listing(mem, code, refs, lo, hi):
    out = []; a = lo
    while a < hi:
        if a in code:
            t, l = code[a]
            if a in refs: out.append('L%04X:' % a)
            out.append('  %04X %-11s %s' % (a, ' '.join('%02X' % mem[a + i] for i in range(l)), t)); a += l
        else:
            b = a; 
            while b < hi and b not in code and b - a < 16: b += 1
            ch = mem[a:b]
            out.append('  %04X db %s  ; %s' % (a, ','.join('%02X' % x for x in ch), bytes(x if 32 <= x < 127 else 46 for x in ch).decode()))
            a = b
    return '\n'.join(out)
if __name__ == '__main__':
    m, c = pickle.load(open('/tmp/claude-0/cpc_game1.pkl', 'rb'))
    cov = pickle.load(open('/tmp/claude-0/cov1.pkl', 'rb'))
    mem = bytearray(m.ram)
    code, refs = trace(mem, [0x226] + sorted(p for p in cov if 0x100 <= p < 0xC000))
    open('/tmp/claude-0/cpc.lst', 'w').write(listing(mem, code, refs, 0x100, 0xC000))
    print(len(code))
