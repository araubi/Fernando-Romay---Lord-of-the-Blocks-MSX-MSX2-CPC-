from sess import Sess
s=Sess(); s.cov=set()
s.run(700); s.key('space'); s.run(800); s.save('../out/cpc_menu.pkl')
s.key('1'); s.run(150); s.save('../out/cpc_game1.pkl')
s.run(4000); s.shot('../out/cpc_g4000.png')
import pickle; pickle.dump(s.cov,open('../out/cov1.pkl','wb')); print(len(s.cov))
