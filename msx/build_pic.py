import sys
from common import *
import head4
SL=0.5
def logo_nidamic(px):
    pts=[(x,y) for y in range(72,90) for x in range(140,190) if px[y][x]==7]
    xp=lambda x,y:int(round(x-SL*(86-y)))
    def letter(x,y):
        v=xp(x,y); return 'D' if v<=156 else ('I' if v<=162 else ('N' if v<=176 else None))
    G={'D':[],'I':[],'N':[]}
    for x,y in pts:
        l=letter(x,y)
        if l: G[l].append((x,y))
    ext={k:(min(xp(x,y) for x,y in v),max(xp(x,y) for x,y in v)) for k,v in G.items()}
    g1=ext['I'][0]-ext['D'][1]; g2=ext['N'][0]-ext['I'][1]
    pos={}; cur=ext['D'][0]
    for k in ('N','I','D'):
        pos[k]=cur; cur+=ext[k][1]-ext[k][0]+(g1 if k=='N' else g2)
    for v in G.values():
        for x,y in v: px[y][x]=1
    for l,v in G.items():
        dd=pos[l]-ext[l][0]
        for x,y in v: px[y][x+dd]=7
SIX=["....######...",
     "..##......#..",
     ".##..........",
     "##...........",
     "##.######....",
     "###......##..",
     "##........##.",
     "##........##.",
     ".##......##..",
     "..########...",
     "............."]
def shirt_six(px, X=51, Y=78):
    # borrar la D (x 51..63, y 78..88) dejando la camiseta blanca y poner un 6 en el mismo trazo
    for y in range(78,89):
        for x in range(51,64): px[y][x]=15
    for r,row in enumerate(SIX):
        for k,ch in enumerate(row):
            if ch=='#': px[Y+r][X+k]=1
def head(px, X0=46, Y0=5):
    h=head4.build()
    for y in range(0,52):
        for x in range(44,89):
            if px[y][x]!=8: px[y][x]=1
    for y in range(h.shape[0]):
        for x in range(h.shape[1]):
            px[Y0+y][X0+x]=15 if h[y,x] else 1
def make():
    d,pos,F=files(); b=F['f1'][3]
    px=decode(b)
    head(px); logo_nidamic(px); shirt_six(px)
    return px,b
if __name__=='__main__':
    px,b=make()
    im=to_img(px); im.save('nuevo.png')
    o=to_img(decode(b))
    s=Image.new('RGB',(1034,384),(70,70,70)); s.paste(o.resize((512,384),Image.NEAREST),(0,0)); s.paste(im.resize((512,384),Image.NEAREST),(522,0)); s.save('antes_despues.png')
    im.crop((30,0,130,100)).resize((600,600),Image.NEAREST).save('zoom.png')
