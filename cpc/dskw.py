"""Escritura de discos CPC: formato SYSTEM (sectores 41h-49h, 2 pistas reservadas), 40 pistas, 1 cara.
Ficheros AMSDOS con cabecera. Directorio con 64 entradas (bloques 0-1), bloques de 1 KB."""
import struct

def amsdos_header(name, ext, data, load, exe, ftype=2):
    h = bytearray(128)
    h[0] = 0
    h[1:9] = name.ljust(8).encode()[:8]; h[9:12] = ext.ljust(3).encode()[:3]
    h[0x12] = ftype
    h[0x15:0x17] = struct.pack('<H', load)
    h[0x18:0x1A] = struct.pack('<H', len(data))
    h[0x1A:0x1C] = struct.pack('<H', exe)
    h[0x40:0x43] = struct.pack('<I', len(data))[:3]
    h[0x43:0x45] = struct.pack('<H', sum(h[:0x43]) & 0xFFFF)
    return bytes(h)

def build(files, tracks=40, label=b'EXTENDED CPC DSK File\r\nDisk-Info\r\n'):
    """files: lista de (nombre8, ext3, bytes_con_cabecera, atributos(dict: ro, sys))"""
    nsec = 9; ssz = 512
    data_secs = (tracks - 2) * nsec
    blocks = data_secs // 2
    img = [bytearray(b'\xE5' * ssz) for _ in range(data_secs)]
    dirb = bytearray(b'\xE5' * 2048)
    nb = 2; de = 0
    for name, ext, content, attr in files:
        recs = (len(content) + 127) // 128
        content = content + b'\x1A' * (recs * 128 - len(content))
        # bloques
        bl = []
        for off in range(0, len(content), 1024):
            chunk = content[off:off + 1024]
            img[2 * nb][:len(chunk[:512])] = chunk[:512]
            if len(chunk) > 512: img[2 * nb + 1][:len(chunk) - 512] = chunk[512:]
            bl.append(nb); nb += 1
            assert nb <= blocks, 'disco lleno'
        # extensiones de 16 bloques (128 registros)
        ex = 0
        while True:
            b16 = bl[ex * 16:(ex + 1) * 16]
            rc = min(128, recs - ex * 128)
            e = bytearray(32)
            e[0] = 0
            e[1:9] = name.ljust(8).encode()[:8]; e[9:12] = ext.ljust(3).encode()[:3]
            if attr.get('ro'): e[9] |= 0x80
            if attr.get('sys'): e[10] |= 0x80
            e[12] = ex; e[15] = rc
            for k, b in enumerate(b16): e[16 + k] = b
            dirb[32 * de:32 * de + 32] = e; de += 1
            ex += 1
            if ex * 128 >= recs: break
    for k in range(4): img[k][:] = dirb[512 * k:512 * k + 512]
    # imagen DSK extendida
    out = bytearray(256)
    out[:len(label)] = label
    out[0x22:0x30] = b'Romay-CPC     '[:14]
    out[0x30] = tracks; out[0x31] = 1
    tsize = 256 + nsec * ssz
    for t in range(tracks): out[0x34 + t] = tsize // 256
    order = [0x41, 0x46, 0x42, 0x47, 0x43, 0x48, 0x44, 0x49, 0x45]
    for t in range(tracks):
        th = bytearray(256)
        th[:12] = b'Track-Info\r\n'
        th[0x10] = t; th[0x11] = 0; th[0x14] = 2; th[0x15] = nsec; th[0x16] = 0x52; th[0x17] = 0xE5
        secdata = bytearray()
        for i, r in enumerate(order):
            th[0x18 + 8 * i:0x20 + 8 * i] = bytes([t, 0, r, 2, 0, 0]) + struct.pack('<H', ssz)
            if t < 2: secdata += b'\xE5' * ssz
            else:
                li = (t - 2) * nsec + (r - 0x41)
                secdata += img[li]
        out += th + secdata
    return bytes(out)
