def put(F3,addr,text,n=10):
    a=addr-0x84D0; t=text.ljust(n).encode('ascii'); assert len(t)==n
    F3[a:a+n]=t
def apply(F1,F2,F3):
    assert bytes(F3[0x9453-0x84D0:0x945D-0x84D0])==b'JUGADOR 1 '
    assert bytes(F3[0x945F-0x84D0:0x9469-0x84D0])==b'MARTIN F. '
    assert bytes(F3[0xA7F2-0x84D0:0xA7FC-0x84D0])==b'MARTIN F. '
    put(F3,0x9453,'ITURRIAGA'); put(F3,0x945F,'F. ROMAY'); put(F3,0xA7F2,'F. ROMAY')
