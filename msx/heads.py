from sprites import entry, p1
IDX=[0x0A,0x16,0x22,0x2E]
def get_head(i):
    a=entry(i); h=p1(a); w=p1(a+1); a+=2
    rows=[]
    for y in range(h):
        r=[p1(a+y*w+k) for k in range(w)]
        line=''
        for x in range(24):
            d=r[x//8]&(0x80>>(x%8)); m=r[3+x//8]&(0x80>>(x%8))
            line+= '#' if d else ('.' if m else 'o')
        rows.append(line)
    return rows
def encode_head(rows):
    out=bytearray()
    for line in rows:
        d=[0,0,0]; m=[0,0,0]
        for x,ch in enumerate(line):
            if ch=='#': d[x//8]|=0x80>>(x%8)
            elif ch=='.': m[x//8]|=0x80>>(x%8)
        out+=bytes(d+m)
    return bytes(out)
if __name__=='__main__':
    for i in IDX+[0x0B]:
        print('== %02X  (# tinta, o borrado, . transparente)'%i)
        for k,l in enumerate(get_head(i)): print('%2d %s'%(k,l))
