import build, random, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100)
rnd=random.Random(int(sys.argv[1])); f=s.c.frames+10
N=int(sys.argv[2])
while f<s.c.frames+N:
    k=rnd.choice(['up','down','left','right','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
m=s.m; c=s.c; r=m.ram
stats={'ok':0,'bad':0,'full':0,'n':[]}
def chk(cpu):
    bad=0
    for row in range(104):
        a=r[0x8118+2*row]|r[0x8119+2*row]<<8
        if r[a:a+64]!=r[0xA568+64*row:0xA568+64*row+64]: bad+=1
    stats['ok' if bad==0 else 'bad']+=1
    stats['n'].append((r[0x7390]-0x54)//4)
    if bad and stats['bad']<4: print('frame',cpu.frames,'bad rows',bad, flush=True); s.img().save('../out/pbad_%d.png'%stats['bad'])
    return False
c.hooks[0x02D9]=chk
bgerr=[0]
def chk2(cpu):   # tras PREST el bufer debe ser el fondo salvo nada (antes de dibujar)
    if r[0x7394]==0 and bytes(r[0xA568:0xBF68])!=bytes(r[0x8B68:0xA568]): bgerr[0]+=1
    return False
c.hooks[0x02A6]=chk2
s.run(N)
import collections
print({k:v for k,v in stats.items() if k!='n'}, 'FULLF', r[0x7394], 'bgerr', bgerr[0], 'entries', collections.Counter(stats['n']).most_common(8), 'PC', hex(c.PC))
s.img().save('../out/pend.png')
