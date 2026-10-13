"""Capacidades por jugador. ITURRIAGA (IX=940Bh): +10% velocidad, energia se gasta +10% mas rapido.
F. ROMAY (IX=9425h): -10% velocidad, energia se gasta un 20% mas lento.
Codigo nuevo en D0D0h (zona muerta de la biblioteca, en el fichero 1)."""
ORG=0xD0D0
CNT={'c1':0xD15C,'c2':0xD15D,'c3':0xD15E,'c4':0xD15F}
def asm():
    code=[]; labels={}; fix=[]
    def L(n): labels[n]=ORG+len(code)
    def b(*v): code.extend(v)
    def w(v): code.extend([v&255,v>>8])
    def jr(op,lab): code.append(op); fix.append((len(code),lab)); code.append(0)
    # ---- SPD: sustituye a CALL 9E47h en el movimiento ----
    L('SPD'); b(0xCD); w(0x9E47); b(0xC0)              # CALL 9E47 / RET NZ
    b(0xDD,0x7D, 0xFE,0x0B); jr(0x28,'P1')             # LD A,IXL / CP 0Bh / JR Z,P1
    b(0x3A); w(CNT['c2']); b(0x3C,0xFE,0x05); jr(0x38,'s1'); b(0xAF)
    L('s1'); b(0x32); w(CNT['c2']); b(0xA7); jr(0x28,'skip'); b(0xAF,0xC9)
    L('skip'); b(0x3C,0xC9)                            # A=1 -> NZ: sin paso extra
    L('P1'); b(0x3A); w(CNT['c1']); b(0x3C,0xFE,0x05); jr(0x38,'s2'); b(0xAF)
    L('s2'); b(0x32); w(CNT['c1']); b(0xA7); jr(0x20,'done')
    b(0xE3,0x7D,0xE3)                                  # EX (SP),HL / LD A,L / EX (SP),HL
    b(0xFE,0xF7); jr(0x28,'dL'); b(0xFE,0x20); jr(0x28,'iL'); b(0xFE,0x86); jr(0x28,'dH')
    b(0x24); jr(0x18,'done')
    L('dL'); b(0x2D); jr(0x18,'done')
    L('iL'); b(0x2C); jr(0x18,'done')
    L('dH'); b(0x25)
    L('done'); b(0xAF,0xC9)
    # ---- THR: sustituye a LD A,07h / LD B,A en el gasto de energia ----
    L('THR'); b(0xDD,0x7D,0xFE,0x0B); jr(0x28,'T1')
    b(0x3A); w(CNT['c4']); b(0x3C,0xFE,0x05); jr(0x38,'s3'); b(0xAF)
    L('s3'); b(0x32); w(CNT['c4']); b(0xA7); jr(0x20,'tdone')
    b(0xDD,0xCB,0x09,0x7E); jr(0x28,'tdone')
    b(0xDD,0x7E,0x09,0xE6,0x7F); jr(0x28,'tdone')
    b(0xDD,0x35,0x09); jr(0x18,'tdone')
    L('T1'); b(0x3A); w(CNT['c3']); b(0x3C,0xFE,0x0A); jr(0x38,'s4'); b(0xAF)
    L('s4'); b(0x32); w(CNT['c3']); b(0xA7); jr(0x20,'tdone')
    b(0xDD,0xCB,0x09,0x7E); jr(0x28,'tdone')
    b(0xDD,0x34,0x09)
    L('tdone'); b(0x3E,0x07,0x47,0xC9)
    for pos,lab in fix:
        d=labels[lab]-(ORG+pos+1); assert -128<=d<=127; code[pos]=d&255
    return bytes(code),labels
def apply(F1,F2,F3):
    code,lab=asm()
    assert ORG+len(code)<=0xD15C, hex(ORG+len(code))
    o=ORG-0xB3B0; F1[o:o+len(code)]=code
    for a in range(0xD15C,0xD160): F1[a-0xB3B0]=0
    for site in (0x9CF4,0x9D1D,0x9D83,0x9DB3):
        i=site-0x84D0; assert bytes(F3[i:i+3])==bytes([0xCD,0x47,0x9E]),hex(site)
        F3[i+1]=lab['SPD']&255; F3[i+2]=lab['SPD']>>8
    i=0x9EE3-0x84D0; assert bytes(F3[i:i+3])==bytes([0x3E,0x07,0x47])
    F3[i:i+3]=bytes([0xCD,lab['THR']&255,lab['THR']>>8])
if __name__=='__main__':
    c,l=asm(); print(len(c),'bytes, fin %04X'%(ORG+len(c)),{k:'%04X'%v for k,v in l.items()})
