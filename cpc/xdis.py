import build, dz80, sys
im=build.make() if __import__("os").environ.get("PATCHED") else build.Img()
mem=im.mem()
def dis(a,n):
    out=[]
    for _ in range(n):
        t,l=dz80.dis(mem,a); out.append('%04X %-12s %s'%(a,' '.join('%02X'%mem[a+i] for i in range(l)),t)); a+=l
    return '\n'.join(out)
if __name__=='__main__':
    for arg in sys.argv[1:]:
        a,n=arg.split(':'); print(dis(int(a,16),int(n))); print('-----')
