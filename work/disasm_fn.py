#!/usr/bin/env python3
"""Disassemble a function from LightBurn.exe by VA, using capstone + PE section map."""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

PATH = '/var/home/Dcs102/lightburn/extracted/app/LightBurn.exe'

def load_secs(data):
    pe_off = struct.unpack_from('<I', data, 0x3c)[0]
    nsec = struct.unpack_from('<H', data, pe_off + 6)[0]
    opt_size = struct.unpack_from('<H', data, pe_off + 20)[0]
    image_base = struct.unpack_from('<Q', data, pe_off + 24 + 24)[0]
    secs = []
    base = pe_off + 24 + opt_size
    for i in range(nsec):
        o = base + i * 40
        name = data[o:o+8].split(b'\x00')[0].decode('latin-1')
        vsize, vaddr, rsize, roff = struct.unpack_from('<IIII', data, o + 8)
        secs.append((name, vaddr, vsize, roff, rsize))
    return image_base, secs

def make_mapper(data):
    image_base, secs = load_secs(data)
    def va2off(va):
        rva = va - image_base
        for name, vaddr, vsize, roff, rsize in secs:
            if vaddr <= rva < vaddr + max(vsize, rsize):
                return roff + (rva - vaddr)
        return None
    return image_base, va2off

def disasm(data, start_va, count=400, stop_on_ret=True):
    image_base, va2off = make_mapper(data)
    off = va2off(start_va)
    if off is None:
        print(f'!! VA {start_va:#x} not in any section'); return
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = False
    out = []
    cur_off, cur_va = off, start_va
    for i in range(count):
        chunk = data[cur_off:cur_off + 16]
        if len(chunk) < 2: break
        found = None
        for ins in md.disasm(chunk, cur_va):
            found = ins
            break
        if found is None: break
        out.append((found.address, found.mnemonic, found.op_str))
        # stop after a RET that ends the function (plain ret / ret imm)
        if stop_on_ret and found.mnemonic == 'ret' and i > 0:
            # peek ahead: if next bytes look like start of new fn (sub/push/lea rbp), stop
            nxt = data[cur_off + found.size:cur_off + found.size + 8]
            if len(nxt) >= 1 and nxt[0] in (0x48, 0x55, 0x53, 0x56, 0x41):
                break
        cur_off += found.size
        cur_va += found.size
    for va, mn, op in out:
        print(f'{va:#x}: {mn} {op}')

if __name__ == '__main__':
    data = open(PATH, 'rb').read()
    start = int(sys.argv[1], 0)
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    disasm(data, start, count)
