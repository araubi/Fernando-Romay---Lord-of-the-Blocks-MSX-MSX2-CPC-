import re
from asm import Asm
L=open('../out/basket_master_msx.asm').read().split('\n')
labels={'CHKRAM':0}; pend=[]
for ln in L:
    m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*):',ln)
    if m: pend.append(m.group(1)); continue
    m=re.search(r';\s*([0-9A-F]{4}):',ln)
    if m:
        for p in pend: labels[p]=int(m.group(1),16)
        pend=[]
for k,v in list(labels.items()):
    if k.startswith('V') or k.startswith('L'): pass
# equates in file
for ln in L:
    m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s+(?:EQU|equ)\s+([0-9A-F]+)h',ln)
    if m: labels[m.group(1)]=int(m.group(2),16)
a=Asm(0,labels); a.labels={}; a.pass2=True
ok=bad=skip=0; fails=[]
for ln in L:
    m=re.match(r'^\s+([A-Z].*?)\s*;\s*([0-9A-F]{4}):\s((?:[0-9A-F]{2} ?)+)',ln)
    if not m: continue
    ins,pc,by=m.group(1),int(m.group(2),16),bytes.fromhex(m.group(3).replace(' ',''))
    if ins.startswith('DB') or ins.startswith('DW'): skip+=1; continue
    # variables Vxxxx sin definir -> por nombre
    ins2=re.sub(r'\bV([0-9A-F]{4})\b',lambda mm:'0x'+mm.group(1),ins)
    try:
        out=bytes(a.ins(ins2,pc))
    except Exception as e:
        bad+=1; fails.append((ins,str(e))); continue
    if out==by: ok+=1
    else: bad+=1; fails.append((ins,by.hex(),out.hex()))
print(ok,bad,skip)
import collections
print(collections.Counter(f[0].split()[0] for f in fails).most_common(20))
for f in fails[:25]: print(f)
