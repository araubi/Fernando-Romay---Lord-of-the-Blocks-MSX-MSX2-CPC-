"""Compresion LZ sencilla para el CPC.
Formato: c=0 fin; 1..127: c bytes literales; 128..255: copia de c-125 bytes desde (destino - o - 1), o = byte siguiente."""
def compress(d):
    out = bytearray(); i = 0; lit = bytearray()
    def flush():
        nonlocal lit
        while lit:
            k = lit[:127]; out.append(len(k)); out.extend(k); lit = lit[127:]
    n = len(d)
    while i < n:
        best = (0, 0)
        for o in range(1, min(256, i) + 1):
            l = 0
            while i + l < n and l < 130 and d[i + l] == d[i + l - o]: l += 1
            if l > best[0]: best = (l, o)
        if best[0] >= 3:
            flush(); out.append(best[0] + 125); out.append(best[1] - 1); i += best[0]
        else:
            lit.append(d[i]); i += 1
    flush(); out.append(0)
    return bytes(out)
def decompress(c):
    out = bytearray(); i = 0
    while True:
        k = c[i]; i += 1
        if k == 0: return bytes(out)
        if k < 128: out += c[i:i + k]; i += k
        else:
            l = k - 125; o = c[i] + 1; i += 1
            for _ in range(l): out.append(out[-o])
