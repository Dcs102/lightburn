#!/usr/bin/env python3
"""Find all direct (E8) and indirect (FF 15) call sites in .text targeting given VAs. Uses pefile."""
import sys, struct
import pefile

def find_calls(data, targets, debug=False):
    pe = pefile.PE(data=data)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    text = None
    for s in pe.sections:
        if s.Name.rstrip(b'\x00').decode('latin1') == '.text':
            text = s
            break
    va = text.VirtualAddress
    roff = text.PointerToRawData
    rsize = min(text.SizeOfRawData, len(data) - roff)
    buf = data[roff:roff + rsize]
    tmap = {int(v, 0): n for v, n in targets}
    results = []
    e8_count = 0
    i = 0
    while i < len(buf):
        b = buf[i]
        va_i = image_base + va + i          # absolute VA of this byte
        if b == 0xE8:
            e8_count += 1
            rel = struct.unpack_from('<i', buf, i+1)[0]
            tgt = va_i + 5 + rel
            if tgt in tmap:
                results.append((va_i, 'E8', tmap[tgt]))
        elif b == 0xFF and i+1 < len(buf) and buf[i+1] == 0x15:
            disp = struct.unpack_from('<i', buf, i+2)[0]
            slot = va_i + 6 + disp
            if slot in tmap:
                results.append((va_i, 'FF15', tmap[slot]))
        i += 1
    if debug:
        print(f'# .text VA=0x{va:x} roff=0x{roff:x} rsize=0x{rsize:x} e8_count={e8_count}', file=sys.stderr)
    return image_base, results

if __name__ == '__main__':
    path = sys.argv[1]
    debug = '--debug' in sys.argv
    args = [a for a in sys.argv[2:] if a != '--debug']
    targets = []
    for a in args:
        name, va = a.split('=')
        targets.append((va, name))
    data = open(path, 'rb').read()
    ib, res = find_calls(data, targets, debug)
    print(f'# image_base=0x{ib:x}')
    for site, kind, name in sorted(res):
        print(f'0x{site:012x}  {kind}  -> {name}')
    print(f'# total call sites: {len(res)}')
