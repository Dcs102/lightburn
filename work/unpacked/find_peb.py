import sys, struct
pid = int(sys.argv[1])
maps = open(f'/proc/{pid}/maps').read().splitlines()
needle = struct.pack('<Q', 0x140000000)
cands = []
for line in maps:
    parts = line.split()
    rng, perm = parts[0], parts[1]
    if 'r' not in perm: continue
    start, end = (int(x,16) for x in rng.split('-'))
    if end - start > 0x4000000: continue  # skip huge regions
    try:
        data = open(f'/proc/{pid}/mem','rb').read()[:0]  # force open
    except Exception: pass
    try:
        with open(f'/proc/{pid}/mem','rb') as f:
            f.seek(start)
            chunk = f.read(end - start)
    except Exception:
        continue
    i = 0
    while True:
        i = chunk.find(needle, i)
        if i < 0: break
        addr = start + i
        peb = addr - 0x10
        # BeingDebugged at peb+2 must be 1; also check plausibility of Ldr ptr
        try:
            with open(f'/proc/{pid}/mem','rb') as f:
                f.seek(peb)
                hdr = f.read(0x30)
            bd = hdr[2]
            ldr = struct.unpack_from('<Q', hdr, 0x18)[0]
            cands.append((peb, bd, hex(ldr)))
        except Exception:
            pass
        i += 1
for peb, bd, ldr in cands:
    print(f"PEB candidate {hex(peb)} BeingDebugged={bd} Ldr={ldr}")
