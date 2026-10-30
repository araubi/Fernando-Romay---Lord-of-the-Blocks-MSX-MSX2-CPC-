import sys, time, cpcemu
F=cpcemu.load_disk('in/orig.dsk')
m,c=cpcemu.boot(F)
shots=[int(x) for x in sys.argv[1].split(',')]
keys={}  # frame -> (row,bit,down)
for spec in sys.argv[2:]:
    f,row,bit,dur=map(int,spec.split(':')); keys.setdefault(f,[]).append((row,bit,1)); keys.setdefault(f+dur,[]).append((row,bit,0))
def snap(cpu):
    f=cpu.frames
    for row,bit,d in keys.get(f,[]):
        if d: m.keys[row]&=~(1<<bit)
        else: m.keys[row]|=1<<bit
    if f in shots:
        cpcemu.render(m,m.galog).save('../out/cpc_%d.png'%f); print('shot',f,'PC %04X'%cpu.PC, m.crtc[:14], m.ink, m.mode,flush=True)
c.snap=snap
t=time.time()
while c.frames<=max(shots): c.step()
print(time.time()-t)
