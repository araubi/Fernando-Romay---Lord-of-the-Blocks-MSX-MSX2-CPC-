import sys, os, statistics
os.environ['MSX_FRAME']='71364'
from timing2 import t2
for f in sys.argv[1:]:
    md,mn,n=t2(f, 450, 1150)
    print('%-12s PAL: mediana %6.0f ciclos = %.2f fotogramas  (media %.2f) n=%d'%(f,md,md/71364,mn/71364,n))
