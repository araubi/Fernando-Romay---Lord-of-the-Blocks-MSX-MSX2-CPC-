"""Imagen del juego para la ROM MSX2 (igual que mk.make pero con msx2_sprite + msx2_regs)."""
import importlib, mk
import charsel_patch, msx2_sprite
def make2():
    _, L, _ = msx2_sprite.build()
    charsel_patch.MSX2 = True; charsel_patch.INIT_ADDR = L['INIT']; charsel_patch.MENUX_ADDR = L['MENUX']
    old = list(mk.mods)
    try:
        mods = [('msx2_sprite' if n == 'sprite_patch' else n) for n in old]
        mods.insert(mods.index('msx2_sprite'), 'msx2_regs')
        mk.mods[:] = mods
        return mk.make()
    finally:
        mk.mods[:] = old; charsel_patch.MSX2 = False
