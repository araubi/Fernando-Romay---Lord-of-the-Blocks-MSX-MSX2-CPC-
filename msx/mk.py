import build_cas as B, importlib
from common import cas_blocks
mods=['menu_patch','names_patch','swap_patch','beard_patch','dunk_patch','romay_patch','jump_fix','court_patch','court_shadow','board_patch','court_msx2','karnov_msx1','controls_patch','user_fix2','user_fix3','user_fix4','stats_patch','shot_patch','sprite_patch','charsel_patch','fixes_patch']
def make(skip=()):
    use=[n for n in mods if n not in skip]
    B.EXTRA=[importlib.import_module(n).apply for n in use]
    d=bytearray(B.build())
    exts=[importlib.import_module(n).ext() for n in use if hasattr(importlib.import_module(n),'ext')]
    if exts:
        assert len(exts)==1
        ext=bytearray(exts[0])
        for n in use:
            mod=importlib.import_module(n)
            if hasattr(mod,'ext_patch'): ext=mod.ext_patch(ext)
        pos,segs=cas_blocks(bytes(d))
        p=pos[3]+8
        s=d[p]|d[p+1]<<8; e=d[p+2]|d[p+3]<<8
        assert (s,e)==(0xB3B0,0xDD18)
        ne=e+len(ext); d[p+2]=ne&255; d[p+3]=ne>>8
        ins=p+6+(e-s+1)
        d[ins:ins]=ext
    return bytes(d)
