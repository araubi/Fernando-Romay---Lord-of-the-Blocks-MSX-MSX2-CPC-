"""MSX1: cinta y ROM ASCII16 de 64 KB del hack a partir de la cinta ORIGINAL (variable ORIG_CAS o ../original/*.cas).
Uso (desde msx/): python3 build_msx1.py   -> ../out/Fernando_Romay_Lord_of_the_Blocks_MSX1.cas y .rom"""
import os, mk, rom_build
os.makedirs('../out', exist_ok=True)
if not os.path.exists('state460.pkl'):
    import subprocess, sys, common
    subprocess.check_call([sys.executable, 'gen_state460.py', common.CAS])
cas = mk.make()
open('../out/Fernando_Romay_Lord_of_the_Blocks_MSX1.cas', 'wb').write(cas)
rom, used = rom_build.build(cas)
open('../out/Fernando_Romay_Lord_of_the_Blocks_MSX1.rom', 'wb').write(rom)
print('MSX1: cinta', len(cas), 'bytes; ROM', len(rom), 'bytes')
