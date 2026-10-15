import pickle, cpcemu
KEY = {'1': (8, 0), '2': (8, 1), '3': (7, 1), '4': (7, 0), 'space': (5, 7), 'up': (0, 0), 'right': (0, 1),
       'down': (0, 2), 'left': (1, 0), 'esc': (8, 2), 'enter': (2, 2), 'ret': (0, 6), 'p': (3, 3),
       'q': (8, 3), 'a': (8, 5), 'o': (4, 2), 'w': (7, 3), 's': (7, 4), 'd': (7, 5), 'shift': (2, 5),
       'j0u': (9, 0), 'j0d': (9, 1), 'j0l': (9, 2), 'j0r': (9, 3), 'j0f1': (9, 4), 'j0f2': (9, 5)}
class Sess:
    def __init__(s, files=None, disk='in/orig.dsk'):
        s.F = files or cpcemu.load_disk(disk)
        s.m, s.c = cpcemu.boot(s.F)
        s.ev = {}; s.c.snap = s._snap; s.shots = {}; s.cov = None; s.wr = None
    def _snap(s, cpu):
        f = cpu.frames
        for (row, bit, d) in s.ev.pop(f, []):
            if d: s.m.keys[row] &= ~(1 << bit)
            else: s.m.keys[row] |= 1 << bit
        if f in s.shots:
            cpcemu.render(s.m, s.m.galog).save(s.shots.pop(f))
        s.lastlog = list(s.m.galog)
    def key(s, name, at=None, dur=6):
        f = s.c.frames + 1 if at is None else at
        row, bit = KEY[name]
        s.ev.setdefault(f, []).append((row, bit, 1)); s.ev.setdefault(f + dur, []).append((row, bit, 0))
    def run(s, nframes):
        end = s.c.frames + nframes; c = s.c
        if s.cov is not None:
            cov = s.cov
            while c.frames < end: cov.add(c.PC); c.step()
        else:
            while c.frames < end: c.step()
    def shot(s, path):
        return cpcemu.render(s.m, getattr(s, 'lastlog', None)).save(path)
    def img(s):
        return cpcemu.render(s.m, getattr(s, 'lastlog', None))
    def save(s, path):
        snap = s.c.snap; s.c.snap = None
        pickle.dump((s.m, s.c), open(path, 'wb')); s.c.snap = snap
    @classmethod
    def load(cls, path):
        o = cls.__new__(cls); o.m, o.c = pickle.load(open(path, 'rb')); o.ev = {}; o.shots = {}; o.cov = None
        o.c.snap = o._snap; o.c.portlog = None; return o
