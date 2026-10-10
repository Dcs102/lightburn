#!/usr/bin/env python3
"""Scan LightBurn.exe .text for call sites of specific imported functions.

Parses the PE import directory to locate IAT slots, then scans .text for:
  - indirect calls: FF 15 <disp32>   (call [rip+disp]) -> target = next_ip + disp
  - direct calls:   E8 <disp32>      (call rel)         -> target = next_ip + disp
and reports every call whose target is one of the requested IAT slots.

Usage: scan_imports.py <pe_file> <import_name> [more_names...]
"""
import struct
import sys


def parse_pe(data):
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe_off:pe_off + 4] == b"PE\0\0", "not PE"
    coff = pe_off + 4
    machine, nsec, _ts, _symoff, nsym, optsize, _ch = struct.unpack_from("<HHIIIHH", data, coff)
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    is64 = (magic == 0x20B)
    # section table
    sec_off = opt + optsize
    sections = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        sections.append((name, va, vsize, roff, rsize))
    # optional header fields. Data directories start at opt+0x5C (PE32) /
    # opt+0x70 (PE32+); the import table is data directory index 1 (+8).
    if is64:
        image_base = struct.unpack_from("<Q", data, opt + 0x18)[0]
        dd = opt + 0x70
    else:
        image_base = struct.unpack_from("<I", data, opt + 0x18)[0]
        dd = opt + 0x5C
    import_rva, import_size = struct.unpack_from("<II", data, dd + 8)
    return {
        "is64": is64, "image_base": image_base, "sections": sections,
        "import_rva": import_rva, "import_size": import_size,
    }


def rva_to_off(info, rva):
    for name, va, vsize, roff, rsize in info["sections"]:
        if va <= rva < va + max(vsize, rsize):
            return roff + (rva - va)
    return None


def parse_imports(data, info):
    """Return list of (dll_name, [(func_name_or_None, ordinal, iat_slot_va), ...])."""
    off = rva_to_off(info, info["import_rva"])
    if off is None:
        return []
    descs = []
    while True:
        orig, ts, fwd, name_rva, iat_rva = struct.unpack_from("<IIIII", data, off)
        if orig == 0 and iat_rva == 0:
            break
        _no = rva_to_off(info, name_rva)
        dll = data[_no:].split(b"\0")[0].decode("latin1") if _no is not None else f"<rva {name_rva:#x}>"
        funcs = []
        base = orig if orig else iat_rva          # original name table RVA
        foff = rva_to_off(info, base)
        idx = 0
        while True:
            if info["is64"]:
                hintname = struct.unpack_from("<Q", data, foff)[0]
            else:
                hintname = struct.unpack_from("<I", data, foff)[0]
            if hintname == 0:
                break
            slot_va = info["image_base"] + iat_rva + idx * (8 if info["is64"] else 4)
            if hintname & 0x80000000:
                funcs.append((None, hintname & 0xFFFF, slot_va))
            else:
                noff = rva_to_off(info, hintname)
                if noff is None:
                    fn = f"<rva {hintname:#x}>"
                else:
                    fn = data[noff + 2:noff + 2 + 64].split(b"\0")[0].decode("latin1")
                funcs.append((fn, None, slot_va))
            foff += 8 if info["is64"] else 4
            idx += 1
        descs.append((dll, funcs))
        off += 20
    return descs


def scan_calls(data, info, target_vas):
    """Scan .text for calls targeting any of target_vas. Return list of (call_site_va, kind)."""
    hits = []
    base = info["image_base"]
    for name, va, vsize, roff, rsize in info["sections"]:
        if name not in (".text",):
            continue
        end = min(roff + rsize, len(data))
        i = roff
        while i < end - 1:
            b0 = data[i]
            va_i = base + (va + (i - roff))
            if b0 == 0xFF and i + 6 <= end and data[i + 1] in (0x15,):
                disp = struct.unpack_from("<i", data, i + 2)[0]
                tgt = va_i + 6 + disp
                if tgt in target_vas:
                    hits.append((va_i, "call [rip+disp]", tgt))
                i += 1
            elif b0 == 0xE8 and i + 5 <= end:
                disp = struct.unpack_from("<i", data, i + 1)[0]
                tgt = va_i + 5 + disp
                if tgt in target_vas:
                    hits.append((va_i, "call rel", tgt))
                i += 1
            else:
                i += 1
    return hits


def main():
    path = sys.argv[1]
    names = set(sys.argv[2:])
    data = open(path, "rb").read()
    info = parse_pe(data)
    imports = parse_imports(data, info)
    wanted = {}
    for dll, funcs in imports:
        for fn, ordn, slot_va in funcs:
            if (fn or f"ord{ordn}") in names:
                wanted[slot_va] = (dll, fn, ordn)
    print(f"# image_base={info['image_base']:#x} is64={info['is64']}")
    for slot_va, (dll, fn, ordn) in sorted(wanted.items()):
        label = fn if fn else f"ordinal {ordn}"
        print(f"# IAT slot {slot_va:#x}  <- {dll}::{label}")
    hits = scan_calls(data, info, set(wanted.keys()))
    for va_i, kind, tgt in sorted(hits):
        dll, fn, ordn = wanted[tgt]
        label = fn if fn else f"ordinal {ordn}"
        print(f"{va_i:#012x}  {kind:16s} -> {dll}::{label}")
    print(f"# total call sites: {len(hits)}")


if __name__ == "__main__":
    main()
