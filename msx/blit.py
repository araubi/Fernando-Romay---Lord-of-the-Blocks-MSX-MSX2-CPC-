import collections
from msx import *
from common import CAS
def trace_blits(cas, start=0, steps=2_100_000, stop_frames=None):
    m,c=load_from_cas(cas)
    calls=[]
    def hk(cpu):
        r=cpu.m.ram
        calls.append(dict(f=cpu.frames, vram=cpu.gHL(), src=r[0xD09A]|r[0xD09B]<<8, h=r[0xD0A0]|r[0xD0A1]<<8,
                          w=r[0xD0A2], pos=r[0xD098]|r[0xD099]<<8, col=r[0xD1BC],
                          ret=[cpu.m.rd(cpu.SP+2*k)|cpu.m.rd(cpu.SP+2*k+1)<<8 for k in range(4)]))
        return False
    c.hooks[0xD288]=hk
    m.slot=lambda page: 0   # permitir gancho fuera de BIOS
    c.run(steps)
    return m,c,calls
if __name__=='__main__':
    m,c,calls=trace_blits(open(CAS,'rb').read())
    agg=collections.OrderedDict()
    for k in calls:
        key=(k['src'],k['vram'],k['w'],k['h'])
        if key not in agg: agg[key]=[k,0]
        agg[key][1]+=1
    for (src,vram,w,h),(k,n) in agg.items():
        print('src %04X -> VRAM %04X  w=%2d bytes h=%3d  pos=%04X col=%02X  x%-3d  ret %s  f%d'%(src,vram,w,h,k['pos'],k['col'],n,' '.join('%04X'%r for r in k['ret']),k['f']))
