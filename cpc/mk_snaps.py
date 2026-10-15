from sess import Sess
s=Sess(); s.cov=set()
s.run(700); s.key('space'); s.run(800); s.save('/tmp/claude-0/cpc_menu.pkl')
s.key('1'); s.run(150); s.save('/tmp/claude-0/cpc_game1.pkl')
s.run(4000); s.shot('/tmp/claude-0/cpc_g4000.png')
import pickle; pickle.dump(s.cov,open('/tmp/claude-0/cov1.pkl','wb')); print(len(s.cov))
