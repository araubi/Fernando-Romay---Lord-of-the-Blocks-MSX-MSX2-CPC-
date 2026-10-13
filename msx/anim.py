import sys
from msx import *
cas=open(sys.argv[1],'rb').read()
m,c=load_from_cas(cas)
shots=[]
def onf(cpu):
    if cpu.frames%12==0 and cpu.frames>=12: shots.append(m.vdp.render().crop((0,0,128,112)))
c.on_frame=onf
c.run(int(sys.argv[2]) if len(sys.argv)>2 else 2_600_000)
cols=6; n=len(shots)
sheet=Image.new('RGB',(130*cols,114*((n+cols-1)//cols)),(60,60,60))
for i,im in enumerate(shots): sheet.paste(im,((i%cols)*130,(i//cols)*114))
sheet=sheet.resize((sheet.width*2,sheet.height*2),Image.NEAREST); sheet.save(sys.argv[3] if len(sys.argv)>3 else 'anim.png')
print('frames',c.frames,'capturas',n)
