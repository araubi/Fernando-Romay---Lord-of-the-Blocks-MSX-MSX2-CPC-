import dsk
def load(path):
    T=dsk.parse(path)
    secs=[]
    for t in range(2,len(T)):
        if T[t] is None: break
        m={s['R']:s['data'][:512] for s in T[t]['secs']}
        for r in range(0x41,0x4a): secs.append(m[r])
    blk=lambda n: (secs[2*n]+secs[2*n+1]) if 2*n+1<len(secs) else b""
    dirb=blk(0)+blk(1)
    files={}
    for i in range(64):
        e=dirb[32*i:32*i+32]
        if e[0]==0xe5: continue
        name=bytes(c&0x7f for c in e[1:9]).decode().strip()+'.'+bytes(c&0x7f for c in e[9:12]).decode().strip()
        ext=e[12]; rc=e[15]; bl=[b for b in e[16:32] if b]
        files.setdefault(name,[]).append((ext,rc,bl,e))
    out={}
    for n,ex in files.items():
        data=b''
        for ext,rc,bl,e in sorted(ex):
            d=b''.join(blk(b) for b in bl)
            data+=d[:rc*128]
        out[n]=(data,[e for *_,e in sorted(ex)])
    return out,secs,blk
if __name__=='__main__':
    import sys
    f,_,_=load(sys.argv[1])
    for n,(d,es) in f.items():
        h=d[:128].ljust(128,b"\0")
        print(repr(n),len(d),'flags',[hex(c) for c in es[0][9:12]],'amsdos type',h[0x12],'load %04X len %04X exec %04X'%(h[0x15]|h[0x16]<<8,h[0x18]|h[0x19]<<8,h[0x1a]|h[0x1b]<<8),'chk',sum(h[:67])&0xffff==h[67]|h[68]<<8)
