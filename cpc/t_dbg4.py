import build
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(30)
c=s.c; m=s.m; ram=m.ram; hits={}
def wr(a,v):
    a&=0xFFFF
    if a>=0xC000:
        o=(a-0xC000)%2048
        row=o//80; col=o%80
        if 3<=row<=15 and col<8:
            k=hex(c.PC); hits[k]=hits.get(k,0)+1
    ram[a]=v&255
m.wr=wr
s.run(400)
print(hits)
print({k:hex(v) for k,v in L.items() if k in ('RECT','re_1','ERASE','CHX','FULLH')})
