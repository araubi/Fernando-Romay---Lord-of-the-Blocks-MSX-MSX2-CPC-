import re, base64, zlib
from msx import *
D=open('/home/claude/w/omr3.xml').read()
SNAPS=[m.start() for m in re.finditer(r'<item id="\d+" version="\d+">\s*<scheduler>',D)]
END=D.find('<events>')
def seg(k): return D[SNAPS[k]:(SNAPS[k+1] if k+1<len(SNAPS) else END)]
def gz(s): return zlib.decompress(base64.b64decode(re.sub(r'\s','',s)))
def tag(s,t,start=0):
    m=re.compile(r'<%s>(.*?)</%s>'%(t,t),re.S).search(s,start); return m.group(1) if m else None
def info(k):
    s=seg(k); r={}
    zi=s.find('<z80 ')
    for t in ('af','bc','de','hl','af2','bc2','de2','hl2','ix','iy','pc','sp','i','r','im'):
        r[t]=int(tag(s,t,zi))
    r['iff1']=tag(s,'iff1',zi)=='true'; r['halt']=int(tag(s,'halt',zi))
    r['slots']=int(tag(s,'primarySlots')); r['portC']=int(tag(s,'portC'))
    t=int(tag(s,'time',s.find('<currentTime>'))); r['time']=t
    vi=s.find('type="VDP"'); reg=tag(s,'registers',vi)
    r['vdpregs']=[int(x) for x in re.findall(r'<item>(\d+)</item>',reg)][:8]
    r['vram']=gz(re.search(r'<vram>\s*<data encoding="gz-base64">(.*?)</data>',s[vi:],re.S).group(1))
    ri=s.find('<name>Main RAM</name>'); r['ram']=gz(re.search(r'<ram encoding="gz-base64">(.*?)</ram>',s[ri:],re.S).group(1))
    return r
def machine(k):
    r=info(k); m=MSX(); c=Z80(m); install_bios(c)
    m.ram[:]=r['ram']; m.vdp.vram[:]=r['vram'][:16384]; m.vdp.reg=r['vdpregs']
    m.ppi_a=r['slots']; m.ppi_c=r['portC']
    c.A,c.F=r['af']>>8,r['af']&255; c.sBC(r['bc']); c.sDE(r['de']); c.sHL(r['hl'])
    c.sh=[r['af2']>>8,r['af2']&255,r['bc2']>>8,r['bc2']&255,r['de2']>>8,r['de2']&255,r['hl2']>>8,r['hl2']&255]
    c.IX,c.IY,c.PC,c.SP,c.I,c.R,c.im=r['ix'],r['iy'],r['pc'],r['sp'],r['i'],r['r'],r['im']
    c.iff=1 if r['iff1'] else 0; c.halt=bool(r['halt'])
    return m,c,r
if __name__=='__main__':
    for k in range(len(SNAPS)):
        r=info(k); print(k,'t=%.1fs'%(r['time']/1e12),'PC %04X SP %04X IM %d I %02X slots %02X vdp %s'%(r['pc'],r['sp'],r['im'],r['i'],r['slots'],r['vdpregs']))
