import pickle, frames, sys
from PIL import Image
CP={0:(40,60,200),1:(0,0,0),2:(255,255,255),3:(255,150,150)}
MP={'.':(40,60,200),'#':(0,0,0),'o':(255,255,255)}
def sheet(C, M, idx, path, sc=3):
    cols=8; cw=60; rh=44
    W=Image.new('RGB',(cols*cw*sc, ((len(idx)+cols-1)//cols)*rh*sc),(90,90,90)); px=W.load()
    for k,i in enumerate(idx):
        ox=(k%cols)*cw; oy=(k//cols)*rh
        if i in C:
            for y,row in enumerate(C[i][1]):
                for x,p in enumerate(row):
                    for a in range(sc):
                        for b in range(sc): px[(ox+x)*sc+a,(oy+y)*sc+b]=CP[p]
        if M and i in M:
            for y,row in enumerate(M[i][1]):
                for x,p in enumerate(row):
                    for a in range(sc):
                        for b in range(sc): px[(ox+x+28)*sc+a,(oy+y)*sc+b]=MP[p]
    W.save(path)
if __name__=='__main__':
    m,c=pickle.load(open('../out/cpc_game1.pkl','rb')); r=bytes(m.ram)
    mx=open('../out/msx_ram.bin','rb').read()
    C=frames.cpc_frames(r,n=75); M=frames.msx_frames(mx,n=75)
    sheet(C,M,range(0,40),'../out/fs1.png'); sheet(C,M,range(40,75),'../out/fs2.png')
