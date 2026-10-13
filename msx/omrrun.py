import sys, collections
from omrload import machine
from msx import Image
def run(k, frames=2500, shots_every=0):
    m,c,r=machine(k); m.slot=lambda p:0
    srcs=collections.OrderedDict(); shots=[]
    def hk(cpu):
        rr=cpu.m.ram; src=rr[0xD09A]|rr[0xD09B]<<8
        st=tuple(cpu.m.rd(cpu.SP+2*j)|cpu.m.rd(cpu.SP+2*j+1)<<8 for j in range(3))
        if (src,st[0]) not in srcs: srcs[(src,st[0])]=(cpu.frames,st,cpu.m.ram[0x940C]&1,cpu.m.ram[0x9426]&1)
        return False
    c.hooks[0xB113]=hk
    def onf(cpu):
        if shots_every and cpu.frames%shots_every==0: shots.append((cpu.frames,m.vdp.render()))
    c.on_frame=onf
    while c.frames<frames: c.step()
    return srcs,shots,c
if __name__=='__main__':
    k=int(sys.argv[1]); srcs,shots,c=run(k,int(sys.argv[2]))
    known={0x7178,0x7452,0x773E,0x772C,0x720A,0x729C,0x732E,0x73C0}
    from sprites import entry,p1
    sp=[(entry(i),entry(i)+2+p1(entry(i))*p1(entry(i)+1),i) for i in range(0x4B)]
    for (src,r0),(f,st,a,b) in srcs.items():
        idx=[('%02X+%d'%(i,src-a_)) for a_,b_,i in sp if a_<=src<b_]
        print('snap%d f%5d src %04X %-12s pila %s'%(k,f,src,idx[:1] or '-',' '.join('%04X'%x for x in st)))
    print('PC final %04X'%c.PC)
