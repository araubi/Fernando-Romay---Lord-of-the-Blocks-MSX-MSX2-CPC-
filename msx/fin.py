from mk import make
from framelog import framelog
out=make(); open('nidamic.cas','wb').write(out)
for s in (3,7):
    log=framelog(out,frames=3000,seed=s); print('seed',s,'events',sum(log.values()),'idx',sorted({a for a,_,_ in log}))
