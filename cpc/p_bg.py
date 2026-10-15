"""Fondo del partido: valla Mirinda | AMSTRAD | ASTRAN PCP, pista del MSX2 con el logo LA84 y Karnov."""
import bg, court, billboard, karnov2
BG, CH = 0x8B68, 0x264A
def apply(im):
    a = bg.decode(im.rd(BG, 0x1A00))
    a = billboard.draw(a)
    a[56:104] = court.court_rows()
    for x in (60, 144): karnov2.paste(a, karnov2.STATIC, x, 16)
    im.poke(BG, bg.encode(a))
    c = bg.decode(im.rd(CH, 21 * 32), w=21, h=32)
    karnov2.paste(c, karnov2.CHEER, 16, 17)
    im.poke(CH, bg.encode(c))
