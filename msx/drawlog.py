from session import *
import collections
def entries(m):
    t={}
    for i in range(0x4A):
        a=0x7760+2*i; e=0x415A+(m.ram[a]|m.ram[a+1]<<8); t[e]=i
    return t
def log(cas, script, f0, f1):
    m,c=load_from_cas(cas); ev=sorted(script); m.slot=lambda p:0
    def onf(cpu):
        while ev and ev[0][0]<=cpu.frames:
            _,k,dn=ev.pop(0); r,b=KEY[k]; m.keys[r]=(m.keys[r]&~(1<<b)) if dn else (m.keys[r]|(1<<b))
    c.on_frame=onf; L=[]
    def hk(cpu):
        if f0<=cpu.frames<f1:
            r=m.ram; src=r[0xD09A]|r[0xD09B]<<8
            ret=m.rd(cpu.SP)|m.rd(cpu.SP+1)<<8
            L.append((cpu.frames,T.get(src,'%04X'%src),r[0xD098],r[0xD099],'%04X'%ret,'%04X'%cpu.IX))
        return False
    T={}
    c.hooks[0xB01C]=hk
    while c.frames<f1:
        if not T and c.frames>=f0-1: T.update(entries(m))
        c.step()
    return L
if __name__=='__main__':
    sc=press('SPACE',120)+press('1',340)+[(420,'RIGHT',True),(470,'RIGHT',False)]
    for x in log(open('nidamic.cas','rb').read(),sc,450,453): print(x)
