from heads import get_head, encode_head, entry
# perfil mirando a la izquierda (0A); 16 es su espejo
PROFILE_LOW = [
 ".......#oooo####........",
 ".......#o#######........",
 "........#oo#####........",
 "........#######.........",
 "........######..........",
 ".........####...........",
 "..........##............",
]
FRONT_LOW = [
 ".......####oo####.......",
 "........###oo###........",
 "........########........",
 "........########........",
 ".........######.........",
 "..........####..........",
]
def heads():
    a=get_head(0x0A)[:9]+PROFILE_LOW
    b=[l[::-1] for l in a]
    c=get_head(0x22)[:10]+FRONT_LOW
    return {0x0A:a,0x16:b,0x22:c}
def apply(F1,F2,F3):
    for i,rows in heads().items():
        assert len(rows)==16 and all(len(r)==24 for r in rows)
        a=entry(i)+2-0x415A          # datos en el fichero 2 (pagina 1 <- 8534h)
        F2[a:a+96]=encode_head(rows)
