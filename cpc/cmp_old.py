"""compara la build actual (256x192) con la anterior (320x200, ../out/oldcpc) en un guion fijo"""
import sys, subprocess, pickle, numpy as np
SC = r'''
import sys, pickle, numpy as np
sys.path.insert(0, DIR); import os; os.chdir(DIR)
import build, cpcemu
from sess import Sess
im=build.make(); s=Sess(files=im.files())
out={}
def snap(tag):
    m=s.m; c=m.crtc; img=np.array(cpcemu.render(m, getattr(s,'lastlog',None)))
    out[tag]=(img, list(c[:14]), list(m.ink[:17]))
STEPS
pickle.dump(out, open(OUT,'wb'))
'''
def run(d, steps, out):
    code = SC.replace('DIR', repr(d)).replace('OUT', repr(out)).replace('STEPS', steps)
    return subprocess.Popen([sys.executable, '-c', code])
def crop(img, crtc):
    if crtc[1] == 40:     # 320x200: columnas 64-575 (modo 2), filas segun R7
        y0 = 8 if crtc[7] == 31 else 0
        return img[y0:y0 + 192, 64:576]
    y0 = 0
    return img[0:192, :]
if __name__ == '__main__':
    steps = open(sys.argv[1]).read()
    a = run('../out/oldcpc', steps, '../out/cmp_old.pkl')
    b = run('/home/claude/cpc', steps, '../out/cmp_new.pkl')
    a.wait(); b.wait()
    A = pickle.load(open('../out/cmp_old.pkl', 'rb')); B = pickle.load(open('../out/cmp_new.pkl', 'rb'))
    from PIL import Image
    for t in A:
        ia, ca, ka = A[t]; ib, cb, kb = B[t]
        x = crop(ia, ca); y = crop(ib, cb)
        d = np.any(x != y, axis=2)
        n = int(d.sum())
        print(t, 'diferencias', n, 'tintas', 'iguales' if ka == kb else (ka, kb), 'borde', ka[16], kb[16])
        if n:
            ys, xs = np.nonzero(d); print('   filas', ys.min(), ys.max(), 'x', xs.min() // 2, xs.max() // 2)
            Image.fromarray(np.concatenate([x, y, (d[:, :, None] * 255).repeat(3, 2).astype(np.uint8)], 0)).save('../out/cmp_%s.png' % t)
