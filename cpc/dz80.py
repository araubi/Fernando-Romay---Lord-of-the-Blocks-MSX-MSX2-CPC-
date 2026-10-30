"""Desensamblador Z80 compacto (documentado + IX/IY). dis(mem, addr) -> (texto, longitud)"""
R = ['b', 'c', 'd', 'e', 'h', 'l', '(hl)', 'a']
RP = ['bc', 'de', 'hl', 'sp']
RP2 = ['bc', 'de', 'hl', 'af']
CC = ['nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm']
ALU = ['add a,', 'adc a,', 'sub ', 'sbc a,', 'and ', 'xor ', 'or ', 'cp ']
ROT = ['rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'sll', 'srl']
IM = ['0', '0', '1', '2', '0', '0', '1', '2']
BLI = {(4, 0): 'ldi', (4, 1): 'cpi', (4, 2): 'ini', (4, 3): 'outi',
       (5, 0): 'ldd', (5, 1): 'cpd', (5, 2): 'ind', (5, 3): 'outd',
       (6, 0): 'ldir', (6, 1): 'cpir', (6, 2): 'inir', (6, 3): 'otir',
       (7, 0): 'lddr', (7, 1): 'cpdr', (7, 2): 'indr', (7, 3): 'otdr'}


def h8(v): return '%02Xh' % v
def h16(v): return '%04Xh' % v
def sd(v): return v - 256 if v > 127 else v


def dis(mem, a):
    rd = lambda o: mem[(a + o) & 0xFFFF]
    op = rd(0); n = 1; ix = None
    if op in (0xDD, 0xFD):
        ix = 'ix' if op == 0xDD else 'iy'
        op = rd(1); n = 2
        if op in (0xDD, 0xFD, 0xED):
            return ('db ' + h8(rd(0)), 1)
    def reg(i, d=None):
        if ix is None: return R[i]
        if i == 6: return '(%s%+d)' % (ix, sd(d))
        if i == 4: return ix + 'h'
        if i == 5: return ix + 'l'
        return R[i]
    def hl(): return ix or 'hl'
    def rpn(p): return hl() if p == 2 else RP[p]
    def rp2(p): return hl() if p == 2 else RP2[p]
    if op == 0xCB:
        if ix:
            d = rd(n); op2 = rd(n + 1); ln = n + 2
            m = '(%s%+d)' % (ix, sd(d))
        else:
            op2 = rd(n); ln = n + 1; m = R[op2 & 7]
        x, y = op2 >> 6, (op2 >> 3) & 7
        if x == 0: return ('%s %s' % (ROT[y], m), ln)
        return ('%s %d,%s' % (['', 'bit', 'res', 'set'][x], y, m), ln)
    if op == 0xED and ix is None:
        op2 = rd(1); x, y, z = op2 >> 6, (op2 >> 3) & 7, op2 & 7; p, q = y >> 1, y & 1
        nn = rd(2) | rd(3) << 8
        if x == 1:
            if z == 0: return (('in %s,(c)' % R[y]) if y != 6 else 'in (c)', 2)
            if z == 1: return (('out (c),%s' % R[y]) if y != 6 else 'out (c),0', 2)
            if z == 2: return (('sbc hl,' if q == 0 else 'adc hl,') + RP[p], 2)
            if z == 3: return (('ld (%s),%s' % (h16(nn), RP[p])) if q == 0 else ('ld %s,(%s)' % (RP[p], h16(nn))), 4)
            if z == 4: return ('neg', 2)
            if z == 5: return ('reti' if y == 1 else 'retn', 2)
            if z == 6: return ('im ' + IM[y], 2)
            return (['ld i,a', 'ld r,a', 'ld a,i', 'ld a,r', 'rrd', 'rld', 'nop*', 'nop*'][y], 2)
        if x == 2 and (y, z) in BLI: return (BLI[(y, z)], 2)
        return ('db EDh,' + h8(op2), 2)
    x, y, z = op >> 6, (op >> 3) & 7, op & 7; p, q = y >> 1, y & 1
    b1 = rd(n); nn = rd(n) | rd(n + 1) << 8
    if x == 0:
        if z == 0:
            if y == 0: return ('nop', n)
            if y == 1: return ("ex af,af'", n)
            t = (a + n + 1 + sd(b1)) & 0xFFFF
            if y == 2: return ('djnz ' + h16(t), n + 1)
            if y == 3: return ('jr ' + h16(t), n + 1)
            return ('jr %s,%s' % (CC[y - 4], h16(t)), n + 1)
        if z == 1:
            if q == 0: return ('ld %s,%s' % (rpn(p), h16(nn)), n + 2)
            return ('add %s,%s' % (hl(), rpn(p)), n)
        if z == 2:
            t = [('ld (bc),a', 0), ('ld a,(bc)', 0), ('ld (de),a', 0), ('ld a,(de)', 0),
                 ('ld (%s),%s' % (h16(nn), hl()), 2), ('ld %s,(%s)' % (hl(), h16(nn)), 2),
                 ('ld (%s),a' % h16(nn), 2), ('ld a,(%s)' % h16(nn), 2)][y]
            return (t[0], n + t[1])
        if z == 3: return (('inc ' if q == 0 else 'dec ') + rpn(p), n)
        if z in (4, 5):
            if ix and y == 6: return (('inc ' if z == 4 else 'dec ') + reg(6, b1), n + 1)
            return (('inc ' if z == 4 else 'dec ') + reg(y), n)
        if z == 6:
            if ix and y == 6: return ('ld %s,%s' % (reg(6, b1), h8(rd(n + 1))), n + 2)
            return ('ld %s,%s' % (reg(y), h8(b1)), n + 1)
        return (['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf'][y], n)
    if x == 1:
        if op == 0x76: return ('halt', n)
        if ix and (y == 6 or z == 6):
            if y == 6: return ('ld %s,%s' % (reg(6, b1), R[z]), n + 1)
            return ('ld %s,%s' % (R[y], reg(6, b1)), n + 1)
        return ('ld %s,%s' % (reg(y), reg(z)), n)
    if x == 2:
        if ix and z == 6: return (ALU[y] + reg(6, b1), n + 1)
        return (ALU[y] + reg(z), n)
    if z == 0: return ('ret ' + CC[y], n)
    if z == 1:
        if q == 0: return ('pop ' + rp2(p), n)
        return (['ret', 'exx', 'jp (%s)' % hl(), 'ld sp,' + hl()][p], n)
    if z == 2: return ('jp %s,%s' % (CC[y], h16(nn)), n + 2)
    if z == 3:
        if y == 0: return ('jp ' + h16(nn), n + 2)
        if y == 2: return ('out (%s),a' % h8(b1), n + 1)
        if y == 3: return ('in a,(%s)' % h8(b1), n + 1)
        return (['', '', '', '', 'ex (sp),' + hl(), 'ex de,hl', 'di', 'ei'][y], n)
    if z == 4: return ('call %s,%s' % (CC[y], h16(nn)), n + 2)
    if z == 5:
        if q == 0: return ('push ' + rp2(p), n)
        return ('call ' + h16(nn), n + 2)
    if z == 6: return (ALU[y] + h8(b1), n + 1)
    return ('rst ' + h8(y * 8), n)


def listing(mem, start, end, labels=None):
    out = []; a = start
    while a < end:
        t, l = dis(mem, a)
        b = ' '.join('%02X' % mem[(a + i) & 0xFFFF] for i in range(l))
        lab = (labels or {}).get(a, '')
        out.append('%04X  %-12s %-8s %s' % (a, b, lab, t)); a += l
    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    data = open(sys.argv[1], 'rb').read()
    base = int(sys.argv[2], 16); s = int(sys.argv[3], 16); e = int(sys.argv[4], 16)
    mem = bytearray(65536); mem[base:base + len(data)] = data[:65536 - base]
    print(listing(mem, s, e))
