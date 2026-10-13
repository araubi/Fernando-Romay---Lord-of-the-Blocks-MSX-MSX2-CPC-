import os, sys
os.environ.setdefault('MSX_FRAME','71364')
from msx2emu import *
from session import KEY, press
def run2(rom, script, frames, shots=()):
    m,c=boot2(rom); m.slot=lambda p:0
    ev=sorted(script); res={}
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
        if cpu.frames in shots: res[cpu.frames]=m.vdp.render()
    c.on_frame=onf
    while c.frames<frames: c.step()
    return m,c,res
if __name__=='__main__':
    rom=open(sys.argv[1],'rb').read()
    sc=press('SPACE',120)+press('1',340)+press(sys.argv[2] if len(sys.argv)>2 else '1',420)
    sc+=[(470,'RIGHT',True),(520,'RIGHT',False),(530,'UP',True),(560,'UP',False)]
    shots=(300,400,480,540,600,700)
    m,c,res=run2(rom,sc,710,shots)
    from PIL import Image
    S=Image.new('RGB',(256*3,192*2))
    for k,f in enumerate(shots): S.paste(res[f],((k%3)*256,(k//3)*192))
    S.resize((256*3*2,192*4),Image.NEAREST).save('/tmp/claude-0/msx2_%s.png'%(sys.argv[2] if len(sys.argv)>2 else '1'))
    print('PC %04X'%c.PC, 'regs',[hex(x) for x in m.vdp.reg[:8]], 'D222=%02X'%m.ram[0xD222], 'ROMSLOT=%02X'%m.ram[0x8000])
