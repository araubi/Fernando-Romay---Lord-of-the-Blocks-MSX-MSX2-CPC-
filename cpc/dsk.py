import sys
def parse(path):
    d=open(path,'rb').read()
    nt,ns=d[0x30],d[0x31]; sizes=[d[0x34+i]*256 for i in range(nt*ns)]
    off=0x100; tracks=[]
    for t,sz in enumerate(sizes):
        if sz==0: tracks.append(None); continue
        h=d[off:off+0x100]; assert h[:10]==b'Track-Info',h[:12]
        n=h[0x15]; secs=[]; p=off+0x100
        for i in range(n):
            e=h[0x18+8*i:0x20+8*i]
            C,H,R,N,s1,s2=e[0],e[1],e[2],e[3],e[4],e[5]; ln=e[6]|e[7]<<8
            secs.append(dict(C=C,H=H,R=R,N=N,st1=s1,st2=s2,len=ln,data=d[p:p+ln])); p+=ln
        tracks.append(dict(tr=h[0x10],side=h[0x11],ssz=h[0x14],gap=h[0x16],fill=h[0x17],secs=secs))
        off+=sz
    return tracks
if __name__=='__main__':
    for i,t in enumerate(parse(sys.argv[1])):
        if t is None: print(i,'-'); continue
        print(i,t['tr'],'N=',t['ssz'],[(s['C'],s['R'],s['N'],s['len'],hex(s['st1']),hex(s['st2'])) for s in t['secs']])
