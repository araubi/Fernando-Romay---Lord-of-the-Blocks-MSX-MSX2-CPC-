import json, os
os.environ.setdefault('MSX_FRAME','71364')
from msx2pal import *
from PIL import Image, ImageDraw, ImageFont
BG=(80,220,230)
def tile(rows, S):
    h=len(rows); im=Image.new('RGB',(24*S,h*S),BG); d=ImageDraw.Draw(im)
    for y,row in enumerate(rows):
        for x,c in enumerate(row):
            col=BG if c=='.' else ((0,0,0) if c=='#' else rgb(c))
            d.rectangle([x*S,y*S,x*S+S-1,y*S+S-1],fill=col)
    return im
def sheet(name, frames, M, fn, S=5, per=12):
    W=24*S+5; H=40*S+18
    rows=(len(frames)+per-1)//per
    im=Image.new('RGB',(W*per+5,H*rows+60),(40,40,40)); d=ImageDraw.Draw(im)
    lay=[]
    for k,i in enumerate(frames):
        x=5+(k%per)*W; y=14+(k//per)*H
        d.text((x,y-12),'%02X'%i,fill=(255,255,0))
        t=tile(resolved(i,M),S); im.paste(t,(x,y)); lay.append([i,x,y,len(F[i])])
    # leyenda
    ly=14+rows*H+8; lx=5
    for idx in (13,2,3,15,1):
        if idx in (2,3) and M is ROM: continue
        d.rectangle([lx,ly,lx+30,ly+30],fill=rgb(idx)); 
        d.text((lx+36,ly+2),'%s (indice %d)'%(NAMES.get(idx,'negro'),idx),fill=(255,255,255))
        d.text((lx+36,ly+16),'RGB MSX2 %d,%d,%d'%PAL2[idx],fill=(180,180,180)); lx+=210
    im.save(fn); return lay
L={}
L['iturriaga']=sheet('ITURRIAGA',ITU_FR,ITU,'/mnt/user-data/outputs/MSX2_sprites_ITURRIAGA.png')
L['romay']=sheet('ROMAY',ROM_FR,ROM,'/mnt/user-data/outputs/MSX2_sprites_ROMAY.png')
json.dump(L,open('/home/claude/w/msx2_sheet_layout.json','w'))
