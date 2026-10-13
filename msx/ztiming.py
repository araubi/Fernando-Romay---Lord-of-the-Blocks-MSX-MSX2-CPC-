"""T-states reales del Z80 en un MSX (con el estado de espera M1: +1 por cada byte de codigo de operacion)."""
U = [4,10,7,6,4,4,7,4,4,11,7,6,4,4,7,4, 8,10,7,6,4,4,7,4,12,11,7,6,4,4,7,4,
     7,10,16,6,4,4,7,4,7,11,16,6,4,4,7,4, 7,10,13,6,11,11,10,4,7,11,13,6,4,4,7,4]
U += [7 if (o & 7) == 6 or ((o >> 3) & 7) == 6 else 4 for o in range(0x40, 0x80)]
U[0x76] = 4
U += [7 if (o & 7) == 6 else 4 for o in range(0x80, 0xC0)]
U += [5,10,10,10,10,11,7,11,5,10,10,0,10,17,7,11, 5,10,10,11,10,11,7,11,5,4,10,11,10,0,7,11,
      5,10,10,19,10,11,7,11,5,4,10,4,10,0,7,11, 5,10,10,4,10,11,7,11,5,6,10,4,10,0,7,11]
assert len(U) == 256
COND_JR = {0x20, 0x28, 0x30, 0x38}
COND_CALL = {0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC}
COND_RET = {0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8}
LEN = {}
def oplen(op):
    if op in (0x01, 0x11, 0x21, 0x31, 0x22, 0x2A, 0x32, 0x3A, 0xC2, 0xC3, 0xCA, 0xCD, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA) or op in COND_CALL: return 3
    if op in (0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x36, 0x3E, 0x10, 0x18, 0xD3, 0xDB) or op in COND_JR or (op & 0xC7) == 0xC6: return 2
    return 1
BIOS = {0x24: 450, 0x0C: 120, 0x14: 120, 0x5F: 2000}        # coste aproximado de rutinas BIOS emuladas
def tstates(c, pc):
    rd = c.m.rd; op = rd(pc); npc = c.PC
    if op in (0xDD, 0xFD):
        op2 = rd(pc + 1)
        if op2 == 0xCB:
            return 21 if (rd(pc + 3) & 0xC0) == 0x40 else 25
        t = U[op2]
        hl_mem = ((op2 & 7) == 6 and 0x40 <= op2 < 0xC0 and op2 != 0x76) or ((op2 >> 3) & 7 == 6 and 0x40 <= op2 < 0x80 and op2 != 0x76) or op2 in (0x34, 0x35, 0x36)
        if hl_mem: t = {0x34: 23, 0x35: 23, 0x36: 19}.get(op2, 19)
        elif op2 in (0x21,): t = 14
        elif op2 in (0x22, 0x2A): t = 20
        elif op2 in (0x09, 0x19, 0x29, 0x39): t = 15
        elif op2 in (0x23, 0x2B): t = 10
        elif op2 == 0xE5: t = 15
        elif op2 == 0xE1: t = 14
        elif op2 == 0xE3: t = 23
        elif op2 == 0xE9: t = 8
        elif op2 == 0xF9: t = 10
        else: t = t + 4
        return t + 2
    if op == 0xCB:
        op2 = rd(pc + 1)
        if (op2 & 7) == 6: return (12 if (op2 & 0xC0) == 0x40 else 15) + 2
        return 8 + 2
    if op == 0xED:
        op2 = rd(pc + 1)
        if op2 in (0xB0, 0xB1, 0xB2, 0xB3, 0xB8, 0xB9, 0xBA, 0xBB):
            return (21 if npc == pc else 16) + 2
        if op2 in (0xA0, 0xA1, 0xA2, 0xA3, 0xA8, 0xA9, 0xAA, 0xAB): return 18
        if (op2 & 0xC7) == 0x40 or (op2 & 0xC7) == 0x41: return 14
        if (op2 & 0xC7) == 0x42: return 17
        if (op2 & 0xC7) == 0x43: return 22
        if op2 in (0x67, 0x6F): return 20
        if op2 in (0x47, 0x4F, 0x57, 0x5F): return 11
        return 10
    t = U[op]
    if op == 0x10: t = 13 if npc != pc + 2 else 8
    elif op in COND_JR: t = 12 if npc != pc + 2 else 7
    elif op in COND_CALL: t = 17 if npc != pc + 3 else 10
    elif op in COND_RET: t = 11 if npc != pc + 1 else 5
    elif op == 0xCD and rd(pc + 1) | rd(pc + 2) << 8 in BIOS: t += BIOS[rd(pc + 1) | rd(pc + 2) << 8]
    return t + 1
