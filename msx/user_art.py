"""Graficos retocados por el usuario (plantillas importadas con s5_import)."""
import os, pickle
PATH = 'user_v1.pkl'
D = pickle.load(open(PATH, 'rb')) if os.path.exists(PATH) else None

def bg(bg):
    """fondo de la pantalla del partido con la cancha, el publico y las canastas del usuario"""
    if not D: return bg
    bg = bg.copy()
    import la84
    bg[56:120, :] = la84.draw(D['cancha'])
    bg[8:56, 32:224] = D['pub']
    bg[8:56, 0:32] = D['hl']
    bg[8:56, 224:256] = D['hr']
    return bg
