"""Ejecuta el juego con un guion de teclas: [(frame, fila, bit, pulsado)] y captura pantallas."""
from msx import *
KEY={'SPACE':(8,0),'LEFT':(8,4),'UP':(8,5),'DOWN':(8,6),'RIGHT':(8,7),'RET':(7,7),
     '0':(0,0),'1':(0,1),'2':(0,2),'3':(0,3),'4':(0,4),'5':(0,5),'6':(0,6),'7':(0,7),'8':(1,0),'9':(1,1)}
def run(cas, script, total_frames, shots_at=(), log=None):
    m,c=load_from_cas(cas)
    ev=sorted(script); shots={}
    def onf(cpu):
        f=cpu.frames
        while ev and ev[0][0]<=f:
            _,k,down=ev.pop(0); r,b=KEY[k]
            m.keys[r]= (m.keys[r] & ~(1<<b)) if down else (m.keys[r] | (1<<b))
        if f in shots_at: shots[f]=m.vdp.render()
    c.on_frame=onf
    while c.frames<total_frames: c.step()
    return m,c,shots
def press(k,f,dur=6): return [(f,k,True),(f+dur,k,False)]
