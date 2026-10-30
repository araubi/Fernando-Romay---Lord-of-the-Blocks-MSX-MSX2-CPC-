"""Lee las hojas coloreadas devueltas por el usuario -> clases por pixel.
Clases: '#' tinta, '.' transparente, 'S' piel, 'R' rojo, 'L' azul, 'W' blanco, 'O' naranja."""
import json, pickle
from PIL import Image
from colorize import F
LAY=json.load(open('msx2_sheet_layout.json'))
REF={'.':(80,220,230),'#':(0,0,0),'S':(255,182,109),'R':(255,36,36),'L':(36,72,218),'W':(255,255,255),'O':(255,109,36)}
def near(p):
    return min(REF,key=lambda k: sum((a-b)**2 for a,b in zip(p,REF[k])))
def parse(fn, key, S=5):
    im=Image.open(fn).convert('RGB'); out={}
    for i,x0,y0,h in LAY[key]:
        rows=[''.join(near(im.getpixel((x0+x*S+2,y0+y*S+2))) for x in range(24)) for y in range(h)]
        out[i]=rows
    return out
if __name__=='__main__':
    U='../art/'
    rom=parse(U+'f1865d6d-image.png','romay'); itu=parse(U+'8d4f1e1f-image.png','iturriaga')
    # coherencia con la forma (tinta/transparente) de los fotogramas
    for name,D in (('itu',itu),('romay',rom)):
        bad=0
        for i,rows in D.items():
            for y,(a,b) in enumerate(zip(rows,F[i])):
                for x,(c,o) in enumerate(zip(a,b)):
                    if (c=='#')!=(o=='#') or (c=='.')!=(o=='.'): bad+=1
        print(name,'pixeles con forma distinta:',bad, 'colores:',sorted(set(''.join(''.join(r) for r in D.values()))))
    pickle.dump({'itu':itu,'romay':rom},open('msx2_classes.pkl','wb'))
