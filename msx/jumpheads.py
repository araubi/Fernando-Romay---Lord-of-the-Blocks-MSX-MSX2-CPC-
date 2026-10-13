from sprites import entry, p1
def grid(i):
    a=entry(i); h=p1(a); w=p1(a+1); a+=2; hw=w//2; rows=[]
    for y in range(h):
        r=[p1(a+y*w+k) for k in range(w)]; line=''
        for x in range(hw*8):
            d=r[x//8]&(0x80>>(x%8)); m=r[hw+x//8]&(0x80>>(x%8))
            line+='#' if d else ('.' if m else 'o')
        rows.append(line)
    return rows
if __name__=='__main__':
    for i in (0x30,0x31,0x32,0x36,0x37,0x38,0x39):
        g=grid(i); print('== %02X'%i)
        for k in range(16): print('%2d %s'%(k,g[k]))
