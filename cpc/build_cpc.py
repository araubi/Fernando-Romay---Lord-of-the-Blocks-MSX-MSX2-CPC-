"""CPC: disco del hack a partir del disco ORIGINAL (variable ORIG_DSK o in/orig.dsk) y de la cinta original de MSX
(para los graficos de saltos y mates que se pasan del MSX).
Uso (desde cpc/): python3 build_cpc.py   -> ../out/Fernando_Romay_Lord_of_the_Blocks_CPC.dsk"""
import os, sys, subprocess
os.makedirs('../out', exist_ok=True)
if not (os.path.exists('msx_ram.bin') and os.path.exists('msxfin_ram.bin')):
    import glob
    cas = os.environ.get('ORIG_CAS') or glob.glob('../original/*.cas')[0]      # cinta ORIGINAL de MSX
    subprocess.check_call([sys.executable, 'gen_msx_ram.py', cas, '../releases/Fernando_Romay_Lord_of_the_Blocks_MSX1.cas'])
import build
d = build.make().dsk()
open('../out/Fernando_Romay_Lord_of_the_Blocks_CPC.dsk', 'wb').write(d)
print('CPC: ../out/Fernando_Romay_Lord_of_the_Blocks_CPC.dsk')
