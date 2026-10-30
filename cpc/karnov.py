import pickle, numpy as np
pub,dp,ch,dc=pickle.load(open('/home/claude/cpc/karnov_src.pkl','rb'))
MAP={1:1,2:3,12:1,15:2,14:2,6:0,10:0,3:0,11:2}
def extract(img, d, y0, y1, x0, x1, grow=1):
    H=y1-y0; W=x1-x0
    out=np.full((H,W),-1,int)
    for y in range(y0,y1):
        xs=[x for x in range(x0,x1) if d[y,x]]
        if not xs: continue
        a=max(x0,min(xs)-grow); b=min(x1-1,max(xs)+grow)
        for x in range(a,b+1): out[y-y0,x-x0]=MAP.get(int(img[y,x]),0)
    return out
def static(): return extract(pub,dp,25,39,26,50)
def cheer(): return extract(ch,dc,17,31,14,44)
if __name__=='__main__':
    from PIL import Image
    P=[(0,0,255),(0,0,0),(255,255,255),(255,128,128)]
    for name,a in (('ks',static()),('kc',cheer())):
        im=np.zeros(a.shape+(3,),np.uint8)
        for y in range(a.shape[0]):
            for x in range(a.shape[1]): im[y,x]=(90,90,90) if a[y,x]<0 else P[a[y,x]]
        Image.fromarray(im).resize((a.shape[1]*16,a.shape[0]*16),Image.NEAREST).save('/tmp/claude-0/%s.png'%name)
