from colorize import *
from PIL import Image, ImageDraw
CL={'S':(255,182,109),'C':(255,36,36),'P':(36,36,218),'M':(255,255,255),'Z':(200,200,200),'B':(255,255,0),'#':(0,0,0),'.':(40,40,90)}
S=8; W=24*S+10
sheet=Image.new('RGB',(W*12,(40*S+20)*6),(60,60,60)); d=ImageDraw.Draw(sheet)
for k,i in enumerate(sorted(F)):
    rows=classify(i); X=(k%12)*W; Y=(k//12)*(40*S+20)
    d.text((X+2,Y+2),'%02X'%i,fill=(255,255,0))
    for y,l in enumerate(rows):
        for x,ch in enumerate(l):
            d.rectangle([X+x*S,Y+14+y*S,X+x*S+S-1,Y+14+y*S+S-1],fill=CL[ch])
sheet.crop((0,0,W*12,(40*S+20)*3)).resize((1600,673)).save('/tmp/claude-0/cl1.png')
sheet.crop((0,(40*S+20)*3,W*12,(40*S+20)*6)).resize((1600,673)).save('/tmp/claude-0/cl2.png')
