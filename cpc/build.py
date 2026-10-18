"""Construccion de la version CPC: imagen de memoria tras la carga + parches -> ficheros y DSK."""
import cpm, dskw, importlib

ORIG = '/home/claude/cpc/in/orig.dsk'
CB0, CB1 = 0x226, 0xA568          # CB.BIN en memoria
AN0 = 0xBFCC                      # ANIPAN.BIN
XB0, XB1 = 0xA568, 0xBFB8   # bloque copiado desde CED9h de ANIPAN al arrancar (original: 15EEh bytes; ampliado
                            # hasta BFB0h para tener codigo en BF68h-BFAFh, por encima del bufer y debajo de la pila)
XSRC = 0xCED9
CA0 = 0x19A                       # CARGA.BIN


class Img:
    def __init__(s):
        f, _, _ = cpm.load(ORIG)
        s.raw = {n: d for n, (d, _) in f.items()}
        hdr = lambda n: s.raw[n][:128]
        body = lambda n: bytearray(s.raw[n][128:128 + (s.raw[n][0x18] | s.raw[n][0x19] << 8)])
        s.cb = body('CB.BIN'); s.an = body('ANIPAN.BIN'); s.ca = body('CARGA.BIN')
        s.bas = s.raw['BASKET.BAS']
        need = XSRC - AN0 + (XB1 - XB0)
        if len(s.an) < need: s.an += bytes(need - len(s.an))
        assert s.ca[0x1DE - CA0:0x1E1 - CA0] == bytes([0x01, 0xEE, 0x15])
        s.ca[0x1DF - CA0] = (XB1 - XB0) & 255; s.ca[0x1E0 - CA0] = (XB1 - XB0) >> 8
        s.extra = []      # ficheros nuevos: (nombre, ext, load, bytes)
        s.free = [list(r) for r in FREE]
        s.labels = {}
    # acceso por direccion de ejecucion
    def _loc(s, a):
        if CB0 <= a < CB1: return s.cb, a - CB0
        if XB0 <= a < XB1: return s.an, XSRC - AN0 + (a - XB0)
        if CA0 <= a < CA0 + len(s.ca): return s.ca, a - CA0
        raise ValueError('direccion fuera de los ficheros: %04X' % a)
    def rd(s, a, n=1):
        buf, o = s._loc(a); assert o + n <= len(buf); return bytes(buf[o:o + n])
    def poke(s, a, data, expect=None):
        data = bytes(data)
        if expect is not None:
            cur = s.rd(a, len(expect))
            assert cur == bytes(expect), 'en %04X se esperaba %s y hay %s' % (a, bytes(expect).hex(), cur.hex())
        buf, o = s._loc(a)
        _, o2 = s._loc(a + len(data) - 1)
        buf[o:o + len(data)] = data
    def place(s, name, src, consts=None, region=None):
        from asm import assemble
        cs = dict(s.labels); cs.update(consts or {})
        code, L, _ = assemble(src, 0x4000, cs)
        n = len(code)
        for r in s.free:
            if region is not None and not (region[0] <= r[0] < region[1]): continue
            if r[1] - r[0] >= n:
                org = r[0]; r[0] += n; break
        else:
            raise RuntimeError('sin hueco para %s (%d bytes)' % (name, n))
        code, L, _ = assemble(src, org, cs)
        assert len(code) == n
        s.poke(org, code)
        s.labels.update(L)
        s.placed = getattr(s, 'placed', []) + [(name, org, n)]
        return L
    def place_many(s, name, srcs):
        """varios trozos que se referencian entre si; cada uno en el primer hueco donde quepa"""
        from asm import assemble
        import re
        names = [set(re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):', x, re.M)) for x in srcs]
        guess = {n: 0x4000 for ns in names for n in ns}
        sizes = []
        for x in srcs:
            cs = dict(s.labels); cs.update(guess)
            code, L, _ = assemble(x, 0x4000, cs); sizes.append(len(code))
        orgs = [None] * len(sizes)
        free = [list(r) for r in s.free]
        order = sorted(range(len(sizes)), key=lambda k: -sizes[k])
        def dfs(i):            # los grandes primero; busqueda con vuelta atras sobre los huecos
            if i == len(order): return True
            k = order[i]; n = sizes[k]; tried = set()
            for r in sorted(free, key=lambda r: r[1] - r[0]):
                sz = r[1] - r[0]
                if sz < n or sz in tried: continue
                tried.add(sz)
                orgs[k] = r[0]; r[0] += n
                if dfs(i + 1): return True
                r[0] -= n
            return False
        if not dfs(0):
            raise RuntimeError('sin hueco para %s (%s bytes); huecos %s' % (name, sizes, [b - a for a, b in free]))
        labs = dict(guess)
        for _ in range(6):
            new = {}; codes = []
            for x, org in zip(srcs, orgs):
                cs = dict(s.labels); cs.update(labs)
                code, L, _ = assemble(x, org, cs); codes.append(code)
                new.update({k: v for k, v in L.items() if k in guess})
            if new == labs: break
            labs = new
        for code, org, n in zip(codes, orgs, sizes):
            assert len(code) == n
            s.poke(org, code)
            s.placed = getattr(s, 'placed', []) + [(name, org, n)]
        s.free = free
        s.labels.update(labs)
        return labs
    def mem(s):
        m = bytearray(65536)
        m[CB0:CB0 + len(s.cb)] = s.cb; m[AN0:AN0 + len(s.an)] = s.an
        m[XB0:XB1] = s.an[XSRC - AN0:XSRC - AN0 + (XB1 - XB0)]
        return m
    def files(s):
        F = {'CB.BIN': bytes(s.cb), 'ANIPAN.BIN': bytes(s.an), 'CARGA.BIN': bytes(s.ca)}
        for n, e, load, d in s.extra: F[n + '.' + e] = bytes(d)
        return F
    def dsk(s):
        L = [('BASKET', 'BAS', s.bas, {'ro': 1})]
        L.append(('CARGA', 'BIN', dskw.amsdos_header('CARGA', 'BIN', s.ca, CA0, 0) + bytes(s.ca), {'ro': 1}))
        L.append(('ANIPAN', 'BIN', dskw.amsdos_header('ANIPAN', 'BIN', s.an, 0x2710, 0) + bytes(s.an), {'ro': 1}))
        L.append(('CB', 'BIN', dskw.amsdos_header('CB', 'BIN', s.cb, CB0, 0) + bytes(s.cb), {'ro': 1}))
        for n, e, load, d in s.extra:
            L.append((n, e, dskw.amsdos_header(n, e, d, load, 0) + bytes(d), {'ro': 1}))
        return dskw.build(L)


FREE = [      # (desde, hasta) huecos de RAM libres dentro de CB.BIN (verificados)
    (0x86EE, 0x8AA8),     # bufer de ceros sin referencias
    (0x7F08, 0x80E7),     # glifos 61h-7Fh (minusculas, sin uso) + restos de un cargador (8000h-80E6h)
    (0x255A, 0x2648),     # copia muerta de la rutina de zoom (sin referencias) + ceros
    (0x1035, 0x109A),     # restos de codigo repetidos tras la cadena 'TIME' (sin referencias; la tabla empieza en 109Ah)
    (0x10C4, 0x10C7),     # entrada de la tabla de saltos sin uso (JP 1BD3h)
    (0xBF68, 0xBFB8),     # entre el bufer de dibujo y la pila (la pila no baja de BFC4h) (se carga con el bloque de arranque)
]

MODS = ['p_names', 'p_stats', 'p_controls', 'p_heads', 'p_jumps', 'p_lcd', 'p_charsel', 'p_bg', 'p_menu', 'p_jordan', 'p_intro', 'p_raster', 'p_bgpack', 'p_partial', 'p_layout', 'p_shot']


def make(mods=None):
    im = Img()
    for name in (mods if mods is not None else MODS):
        importlib.import_module(name).apply(im)
    return im
