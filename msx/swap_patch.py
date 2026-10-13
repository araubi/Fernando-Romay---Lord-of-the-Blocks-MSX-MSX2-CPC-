PAIRS=[(0x0A,0x0B),(0x16,0x17),(0x22,0x23),(0x2E,0x2F)]
def apply(F1,F2,F3):
    base=0x7760-0x415A
    for a,b in PAIRS:
        ia,ib=base+2*a,base+2*b
        ea,eb=bytes(F2[ia:ia+2]),bytes(F2[ib:ib+2])
        F2[ia:ia+2]=eb; F2[ib:ib+2]=ea
