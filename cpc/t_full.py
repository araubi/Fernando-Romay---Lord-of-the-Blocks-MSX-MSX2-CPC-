import scrmap
"""Partido completo (1 jugador) con capturas en el descanso, la segunda parte, el final y el menu."""
import build, random, sys
from sess import Sess
im=build.make(); L=im.labels
s=Sess(files=im.files()); s.run(700); s.key('space'); s.run(800)
s.key('1'); s.run(60); s.key('1'); s.run(100); s.key('1'); s.run(100)
m=s.m; c=s.c; r=m.ram
rnd=random.Random(int(sys.argv[1])); N=int(sys.argv[2]); f=c.frames+10
while f<c.frames+N:
    k=rnd.choice(['up','down','left','right','space','space']); d=rnd.randint(5,60); s.key(k,at=f,dur=d); f+=d+rnd.randint(1,8)
ev=[]
def mk(n):
    def h(cpu): ev.append((cpu.frames,n)); return False
    return h
for n in ('STAT2','MENU2','SETUP'): c.hooks[L[n]]=mk(n)
pend=[]; last=None; bad=0
end=c.frames+N
while c.frames<end:
    c.step()
    if not scrmap.code_ok(c.PC): bad+=1
    if ev and ev[-1] is not last:
        last=ev[-1]; print(last, flush=True); pend += [(last[0]+k, '%s_%d_%d'%(last[1],last[0],k)) for k in (150,400)]
    if pend and c.frames>=pend[0][0]:
        _,name=pend.pop(0); s.shot('../out/full_%s.png'%name)
print('bad',bad); s.shot('../out/full_end.png'); s.save('../out/full_end.pkl')
