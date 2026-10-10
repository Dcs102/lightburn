import sys, struct
pid = int(sys.argv[1])
maps = open(f'/proc/{pid}/maps').read().splitlines()
needle = struct.pack('<Q', 0x140000000)
best = []
for line in maps:
    parts = line.split()
    rng, perm = parts[0], parts[1]
    if 'r' not in perm: continue
    start, end = (int(x,16) for x in rng.split('-'))
    if end - start > 0x8000000: continue
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
        peb = start + i - 0x10
        try:
            with open(f'/proc/{pid}/mem','rb') as f:
                f.seek(peb)
                hdr = f.read(0x40)
            bd = hdr[2]
            ldr = struct.unpack_from('<Q', hdr, 0x18)[0]
            pp  = struct.unpack_from('<Q', hdr, 0x20)[0]
            if bd == 1 and (ldr >> 44) in (0x7f, 0x55):
                # verify PEB_LDR_DATA: first QWORD should be ldr+0x30 (exe entry first in load order)
                try:
                    with open(f'/proc/{pid}/mem','rb') as f:
                        f.seek(ldr)
                        ldrd = f.read(0x40)
                    flink = struct.unpack_from('<Q', ldrd, 0)[0]
                    ok = (flink == ldr + 0x30)
                except Exception:
                    ok = False
                best.append((peb, hex(ldr), hex(pp), ok))
        except Exception:
            pass
        i += 1
for peb, ldr, pp, ok in best:
    print(f"PEB={hex(peb)} Ldr={ldr} PP={pp} ldr_ok={ok}")
if not best:
    print("NO CANDIDATES")
