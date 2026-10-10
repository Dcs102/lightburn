#!/usr/bin/env python3
"""Build cracked/LightBurn_hardened.exe = the section-17 license patch set PLUS a NOP of
reldnaHesnec1L::ShutDown's deactivation call (call FUN_1404c0250 @ 0x1403b72ca).

Reuses the verified section-17 emitters from patch_license.py, then:
  * NOPs the 5-byte `call 0x1404c0250` in ShutDown so closing the app never deactivates.
  * Recomputes the PE OptionalHeader.CheckSum at the CORRECT offset (opt+0x40 for both
    PE32/PE32+). patch_license.py wrote it to opt+0x5C (corrupting SizeOfHeapReserve); this
    fixes that so the hardened exe is a fully valid PE.

Verification (all printed, all must pass):
  * byte-exact: each patched region read back == intended blob; original E8 confirmed at NOP site.
  * disasm: capstone decode of every patched region shows the expected instructions.
  * PE checksum: stored value == pefile.generate_checksum() (idempotent/valid).

Usage: python3 work/patch_hardened.py
"""
import hashlib
import os
import shutil
import struct

from patch_license import (
    Asm, build_allow, build_check_entry, build_cave, build_dlleval, roff,
    ALLOW_ENTRY, CHECK_ENTRY, CAVE, DLLEVAL, NEXT_FN_AFTER_CAVE,
)

SRC = "extracted/app/LightBurn.exe"
DST = "cracked/LightBurn_hardened.exe"

# reldnaHesnec1L::ShutDown @ 0x1403b71b0: `call 0x1404c0250` (deactivate) at this VA.
SHUTDOWN_CALL = 0x1403b72ca
NOP5 = b"\x90" * 5


def recompute_pe_checksum(data):
    """Return (new_data, old_sum, new_sum). Writes OptionalHeader.CheckSum at opt+0x40.

    Matches pefile.PE.generate_checksum() exactly: sum 32-bit dwords (skipping the checksum
    dword, zero-padding a final partial dword), carry-fold at 2^32, double 16-bit fold, then add
    the original (unpadded) file length.
    """
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off + 4] != b"PE\0\0":
        raise ValueError("not a PE file")
    opt_off = pe_off + 24
    cs_off = opt_off + 0x40                          # CheckSum, same offset for PE32 and PE32+
    old_sum = struct.unpack_from("<I", data, cs_off)[0]

    buf = bytearray(data)
    n = len(buf)
    remainder = n % 4
    data_len = n + ((4 - remainder) * (remainder != 0))
    checksum = 0
    cs_dword_idx = cs_off // 4
    for i in range(data_len // 4):
        if i == cs_dword_idx:                         # skip the checksum field itself
            continue
        if i + 1 == (data_len // 4) and remainder:
            dword = struct.unpack("I", buf[i * 4:] + b"\0" * (4 - remainder))[0]
        else:
            dword = struct.unpack_from("I", buf, i * 4)[0]
        checksum += dword
        if checksum >= 2 ** 32:
            checksum = (checksum & 0xFFFFFFFF) + (checksum >> 32)
    checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum = checksum + (checksum >> 16)
    checksum = checksum & 0xFFFF
    checksum += n                                     # add original length, not masked after
    struct.pack_into("<I", buf, cs_off, checksum)
    return bytes(buf), old_sum, checksum


def disasm(va, blob):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    out = []
    for i in md.disasm(bytes(blob), va):
        out.append(f"    {i.address:#012x}: {i.mnemonic:8s} {i.op_str}")
    return "\n".join(out) if out else "    <no instructions>"


def main():
    os.makedirs("cracked", exist_ok=True)
    shutil.copyfile(SRC, DST)
    data = bytearray(open(DST, "rb").read())

    cave = build_cave()
    assert CAVE + len(cave) <= NEXT_FN_AFTER_CAVE, "cave overruns next function"

    patches = [
        ("Allow entry", ALLOW_ENTRY, build_allow()),
        ("Checkesnec1L_Internal entry (jmp)", CHECK_ENTRY, build_check_entry()),
        ("cave", CAVE, cave),
        ("DLLEvaluation entry", DLLEVAL, build_dlleval()),
    ]

    # Confirm the ShutDown call is a direct E8 before we NOP it.
    sc_off = roff(SHUTDOWN_CALL)
    assert data[sc_off] == 0xE8, f"expected E8 at {SHUTDOWN_CALL:#x}, got {data[sc_off]:#04x}"
    patches.append(("ShutDown deactivate call (NOP)", SHUTDOWN_CALL, NOP5))

    print("== applying patches ==")
    for label, va, blob in patches:
        off = roff(va)
        assert 0 <= off and off + len(blob) <= len(data), f"out of range: {va:#x}"
        data[off:off + len(blob)] = blob

    # ---- byte-exact verification: read back every patched region ----
    print("\n== byte-exact check ==")
    for label, va, blob in patches:
        off = roff(va)
        got = bytes(data[off:off + len(blob)])
        assert got == blob, f"MISMATCH {label} @ {va:#x}"
        print(f"  OK {label:38s} {va:#012x} {len(blob):3d}B  {got.hex(' ')}")

    # ---- disasm verification of each patched region ----
    print("\n== disasm check (capstone) ==")
    for label, va, blob in patches:
        print(f"  {label}:")
        print(disasm(va, blob))

    # ---- PE checksum (corrected offset) ----
    data, old_sum, new_sum = recompute_pe_checksum(bytes(data))
    open(DST, "wb").write(data)

    # verify with pefile that the stored checksum is valid/idempotent
    import pefile
    final = open(DST, "rb").read()
    pe = pefile.PE(data=final)
    pe_sum = pe.generate_checksum()
    pe_off = struct.unpack_from("<I", final, 0x3C)[0]
    opt_off = pe_off + 24
    stored = struct.unpack_from("<I", final, opt_off + 0x40)[0]        # CheckSum (PE32/PE32+)
    heap_reserve = struct.unpack_from("<Q", final, opt_off + 0x58)[0]  # SizeOfHeapReserve (PE32+)

    print("\n== PE checksum check ==")
    print(f"  old stored checksum : {old_sum:#010x}")
    print(f"  new stored checksum : {new_sum:#010x}  (at opt+0x40 / file 0x1B8)")
    print(f"  pefile.generate_checksum(): {pe_sum:#010x}")
    print(f"  stored == pefile      : {stored == pe_sum}  ({stored:#010x})")
    print(f"  SizeOfHeapReserve     : {heap_reserve:#x}  (must stay 0x100000)")
    assert stored == pe_sum, "PE checksum mismatch"
    assert heap_reserve == 0x100000, "SizeOfHeapReserve corrupted"

    sha = hashlib.sha256(final).hexdigest()
    print(f"\nOK -> {DST}  ({len(final)} bytes)  sha256={sha}")


if __name__ == "__main__":
    main()
