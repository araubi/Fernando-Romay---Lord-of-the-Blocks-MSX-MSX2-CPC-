import pickle
from heads import encode_head
EDITS=pickle.load(open('/home/claude/w/user_sheet_edits4.pkl','rb'))
def apply(F1,F2,F3):
    def p1(a): return F2[a-0x415A]
    for i,rows in EDITS.items():
        a=0x7760+2*i; e=0x415A+(p1(a)|p1(a+1)<<8)       # tabla ya intercambiada
        assert p1(e)==len(rows)
        d=encode_head(rows); F2[e+2-0x415A:e+2-0x415A+len(d)]=d
