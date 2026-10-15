"""Menu: cabecera FERNANDO ROMAY / LORD OF THE BLOCKS y (C) NIDAMIC."""
SRC = """
TITLE:
  ld hl,0C01h
  ld de,TT1
  call 10BBh
  ld hl,0B03h
  jp 10BBh
TT1: db 'FERNANDO  ROMAY',0FFh,'LORD OF THE BLOCKS',0FFh
"""
def apply(im):
    from p_charsel import asm_str
    L = im.place('title', asm_str(SRC))
    im.poke(0x21C8, [0x21, 0x01, 0x05, 0x11, 0x52, 0x23, 0xCD, L['TITLE'] & 255, L['TITLE'] >> 8],
            [0x21, 0x01, 0x05, 0x11, 0x52, 0x23, 0xCD, 0xBB, 0x10])
    im.poke(0x23AC, b'NIDAMIC', b'DINAMIC')
