"""Ensamblador Z80 minimo (dos pasadas) para los parches.
Sintaxis: una instruccion por linea, 'etiqueta:' opcional, ';' comentarios.
Numeros: 0x1F, 1Fh, 31, $1F. Expresiones python simples con etiquetas/constantes.
Directivas: org N, db a,b,..., dw a,..., ds n, equ (NOMBRE equ valor)."""
import re

R8 = {'B': 0, 'C': 1, 'D': 2, 'E': 3, 'H': 4, 'L': 5, '(HL)': 6, 'A': 7}
R16 = {'BC': 0, 'DE': 1, 'HL': 2, 'SP': 3}
R16P = {'BC': 0, 'DE': 1, 'HL': 2, 'AF': 3}
CC = {'NZ': 0, 'Z': 1, 'NC': 2, 'C': 3, 'PO': 4, 'PE': 5, 'P': 6, 'M': 7}
ALU = {'ADD': 0, 'ADC': 1, 'SUB': 2, 'SBC': 3, 'AND': 4, 'XOR': 5, 'OR': 6, 'CP': 7}
ROT = {'RLC': 0, 'RRC': 1, 'RL': 2, 'RR': 3, 'SLA': 4, 'SRA': 5, 'SRL': 7}
SIMPLE = {'NOP': [0], 'RLCA': [7], 'RRCA': [0x0F], 'RLA': [0x17], 'RRA': [0x1F], 'CPL': [0x2F], 'SCF': [0x37],
          'CCF': [0x3F], 'HALT': [0x76], 'DI': [0xF3], 'EI': [0xFB], 'EXX': [0xD9], 'NEG': [0xED, 0x44],
          'LDIR': [0xED, 0xB0], 'LDDR': [0xED, 0xB8], 'LDI': [0xED, 0xA0], 'OUTI': [0xED, 0xA3],
          'OTIR': [0xED, 0xB3], 'RET': [0xC9], 'RLD': [0xED, 0x6F], 'RRD': [0xED, 0x67],
          'INI': [0xED, 0xA2], 'INIR': [0xED, 0xB2], 'IND': [0xED, 0xAA], 'INDR': [0xED, 0xBA],
          'OUTD': [0xED, 0xAB], 'OTDR': [0xED, 0xBB], 'RETI': [0xED, 0x4D], 'DAA': [0x27],
          'LDD': [0xED, 0xA8], 'CPI': [0xED, 0xA1], 'CPIR': [0xED, 0xB1]}


class Asm:
    def __init__(s, org=0, consts=None):
        s.org = org; s.consts = dict(consts or {})

    def num(s, t):
        t = t.strip()
        t = re.sub(r'\$([0-9A-Fa-f]+)', r'0x\1', t)
        t = re.sub(r'\b([0-9A-Fa-f]+)[hH]\b', r'0x\1', t)
        env = dict(s.consts); env.update(s.labels)
        try:
            return int(eval(t, {}, env))
        except NameError:
            if s.pass2: raise
            return 0

    def idx(s, op):
        m = re.fullmatch(r'\((I[XY])\s*([+-].*)?\)', op.replace(' ', ''))
        if not m: return None
        d = s.num(m.group(2)) if m.group(2) else 0
        return (0xDD if m.group(1) == 'IX' else 0xFD), d & 255

    def ins(s, line, pc):
        line = line.strip()
        if not line: return []
        sp = line.split(None, 1); mn = sp[0].upper(); rest = sp[1] if len(sp) > 1 else ''
        ops = [o.strip() for o in re.split(r',(?![^()]*\))', rest)] if rest else []
        U = [o.upper().replace(' ', '') for o in ops]
        if mn == 'DB': return [s.num(o) & 255 for o in ops]
        if mn == 'DW':
            out = []
            for o in ops: v = s.num(o); out += [v & 255, (v >> 8) & 255]
            return out
        if mn == 'DS': return [0] * s.num(ops[0])
        if mn in SIMPLE and not ops: return SIMPLE[mn]
        def r8(o): return R8.get(o)
        def ixh(o):
            return {'IXH': (0xDD, 4), 'IXL': (0xDD, 5), 'IYH': (0xFD, 4), 'IYL': (0xFD, 5)}.get(o)
        def nn(o): v = s.num(o); return [v & 255, (v >> 8) & 255]
        def mem(o): return o.startswith('(') and o.endswith(')')
        if mn == 'LD':
            a, b = U
            if r8(a) is not None and r8(b) is not None and not (a == b == '(HL)'): return [0x40 | r8(a) << 3 | r8(b)]
            ia, ib = s.idx(a), s.idx(b)
            if ia and r8(b) is not None and b != '(HL)': return [ia[0], 0x70 | r8(b), ia[1]]
            if ib and r8(a) is not None and a != '(HL)': return [ib[0], 0x46 | r8(a) << 3, ib[1]]
            if ia: return [ia[0], 0x36, ia[1], s.num(ops[1]) & 255]
            if a in ('IX', 'IY'):
                p = 0xDD if a == 'IX' else 0xFD
                if mem(b): return [p, 0x2A] + nn(ops[1][1:-1])
                return [p, 0x21] + nn(ops[1])
            if b in ('IX', 'IY') and mem(a): return [0xDD if b == 'IX' else 0xFD, 0x22] + nn(ops[0][1:-1])
            if a == 'A' and b == '(BC)': return [0x0A]
            if a == 'A' and b == '(DE)': return [0x1A]
            if a == '(BC)' and b == 'A': return [0x02]
            if a == '(DE)' and b == 'A': return [0x12]
            if a == 'A' and b in ('I', 'R'): return [0xED, 0x57 if b == 'I' else 0x5F]
            if a == 'SP' and b == 'HL': return [0xF9]
            if ixh(a) and r8(b) is not None and b not in ('(HL)', 'H', 'L'): p, c = ixh(a); return [p, 0x40 | c << 3 | r8(b)]
            if ixh(b) and r8(a) is not None and a not in ('(HL)', 'H', 'L'): p, c = ixh(b); return [p, 0x40 | r8(a) << 3 | c]
            if ixh(a): p, c = ixh(a); return [p, 0x06 | c << 3, s.num(ops[1]) & 255]
            if a == 'A' and mem(b): return [0x3A] + nn(ops[1][1:-1])
            if mem(a) and b == 'A': return [0x32] + nn(ops[0][1:-1])
            if a == 'HL' and mem(b): return [0x2A] + nn(ops[1][1:-1])
            if mem(a) and b == 'HL': return [0x22] + nn(ops[0][1:-1])
            if a in R16 and mem(b): return [0xED, 0x4B | R16[a] << 4] + nn(ops[1][1:-1])
            if mem(a) and b in R16: return [0xED, 0x43 | R16[b] << 4] + nn(ops[0][1:-1])
            if a in R16: return [0x01 | R16[a] << 4] + nn(ops[1])
            if r8(a) is not None: return [0x06 | r8(a) << 3, s.num(ops[1]) & 255]
        if mn in ALU:
            if len(U) == 2 and U[0] == 'HL':
                if mn == 'ADD': return [0x09 | R16[U[1]] << 4]
                if mn == 'SBC': return [0xED, 0x42 | R16[U[1]] << 4]
                if mn == 'ADC': return [0xED, 0x4A | R16[U[1]] << 4]
            if len(U) == 2 and U[0] in ('IX', 'IY') and mn == 'ADD':
                r = {'BC': 0, 'DE': 1, U[0]: 2, 'SP': 3}[U[1]]
                return [0xDD if U[0] == 'IX' else 0xFD, 0x09 | r << 4]
            o = U[-1]; oo = ops[-1]
            if r8(o) is not None: return [0x80 | ALU[mn] << 3 | r8(o)]
            if ixh(o): p, c = ixh(o); return [p, 0x80 | ALU[mn] << 3 | c]
            i = s.idx(o)
            if i: return [i[0], 0x86 | ALU[mn] << 3, i[1]]
            return [0xC6 | ALU[mn] << 3, s.num(oo) & 255]
        if mn in ('INC', 'DEC'):
            o = U[0]; dec = mn == 'DEC'
            if o in R16: return [(0x0B if dec else 0x03) | R16[o] << 4]
            if o in ('IX', 'IY'): return [0xDD if o == 'IX' else 0xFD, 0x2B if dec else 0x23]
            if r8(o) is not None: return [(0x05 if dec else 0x04) | r8(o) << 3]
            if ixh(o): p, c = ixh(o); return [p, (0x05 if dec else 0x04) | c << 3]
            i = s.idx(o)
            if i: return [i[0], 0x35 if dec else 0x34, i[1]]
        if mn in ('PUSH', 'POP'):
            o = U[0]; base = 0xC5 if mn == 'PUSH' else 0xC1
            if o in ('IX', 'IY'): return [0xDD if o == 'IX' else 0xFD, base | 0x20]
            return [base | R16P[o] << 4]
        if mn == 'EX':
            if U == ['DE', 'HL']: return [0xEB]
            if U == ['(SP)', 'HL']: return [0xE3]
            if U == ["AF", "AF'"]: return [0x08]
        if mn == 'JP':
            if U[0] == '(HL)': return [0xE9]
            if U[0] in ('(IX)', '(IY)'): return [0xDD if U[0] == '(IX)' else 0xFD, 0xE9]
            if len(U) == 2: return [0xC2 | CC[U[0]] << 3] + nn(ops[1])
            return [0xC3] + nn(ops[0])
        if mn == 'CALL':
            if len(U) == 2: return [0xC4 | CC[U[0]] << 3] + nn(ops[1])
            return [0xCD] + nn(ops[0])
        if mn == 'RET' and ops: return [0xC0 | CC[U[0]] << 3]
        if mn in ('JR', 'DJNZ'):
            t = s.num(ops[-1]); d = t - (pc + 2)
            if s.pass2 and not -128 <= d <= 127: raise ValueError('salto fuera de rango: ' + line)
            if mn == 'DJNZ': return [0x10, d & 255]
            if len(U) == 2: return [{'NZ': 0x20, 'Z': 0x28, 'NC': 0x30, 'C': 0x38}[U[0]], d & 255]
            return [0x18, d & 255]
        if mn in ROT:
            o = U[0]
            if r8(o) is not None: return [0xCB, ROT[mn] << 3 | r8(o)]
            i = s.idx(o)
            if i: return [i[0], 0xCB, i[1], ROT[mn] << 3 | 6]
        if mn in ('BIT', 'SET', 'RES'):
            b = s.num(ops[0]); o = U[1]; base = {'BIT': 0x40, 'RES': 0x80, 'SET': 0xC0}[mn]
            if r8(o) is not None: return [0xCB, base | b << 3 | r8(o)]
            i = s.idx(o)
            if i: return [i[0], 0xCB, i[1], base | b << 3 | 6]
        if mn == 'OUT':
            if U[1] == 'A' and U[0] != '(C)': return [0xD3, s.num(ops[0][1:-1]) & 255]
            if U[0] == '(C)': return [0xED, 0x41 | r8(U[1]) << 3]
        if mn == 'IN':
            if U[0] == 'A' and U[1] != '(C)': return [0xDB, s.num(ops[1][1:-1]) & 255]
            if U[1] == '(C)': return [0xED, 0x40 | r8(U[0]) << 3]
        if mn == 'RST': return [0xC7 | (s.num(ops[0]) & 0x38)]
        if mn == 'IM': return [0xED, {0: 0x46, 1: 0x56, 2: 0x5E}[s.num(ops[0])]]
        if mn == 'JP' and U and U[0] in ('(IX)', '(IY)'): return [0xDD if U[0] == '(IX)' else 0xFD, 0xE9]
        raise ValueError('no se: ' + line)

    def assemble(s, src):
        s.labels = {}
        for s.pass2 in (False, True):
            pc = s.org; out = bytearray(); s.lines = []
            for raw in src.split('\n'):
                line = raw.split(';')[0].rstrip()
                if not line.strip(): continue
                m = re.match(r'\s*([A-Za-z_][A-Za-z_0-9]*)\s+equ\s+(.*)$', line, re.I)
                if m: s.consts[m.group(1)] = s.num(m.group(2)); continue
                m = re.match(r'\s*([A-Za-z_][A-Za-z_0-9]*):(.*)$', line)
                if m:
                    s.labels[m.group(1)] = pc; line = m.group(2)
                    if not line.strip(): continue
                if re.match(r'\s*org\s', line, re.I):
                    pc = s.num(line.split(None, 1)[1]); s.org = pc if not out else s.org
                    if out: raise ValueError('org en medio')
                    continue
                b = s.ins(line, pc)
                s.lines.append((pc, bytes(b), line.strip()))
                out += bytes(b); pc += len(b)
        return bytes(out)

    def listing(s):
        return '\n'.join('%04X  %-12s %s' % (pc, b.hex(' '), t) for pc, b, t in s.lines)


def assemble(src, org=0, consts=None):
    a = Asm(org, consts); code = a.assemble(src); return code, a.labels, a
