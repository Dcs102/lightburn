#!/usr/bin/env python3
"""Patch LightBurn.exe to force a fully-licensed, all-features state.

Implements NOTES.md section 16g (verified against Ghidra + objdump):
  1. Allow()               @ 0x1403a22f0 -> Isla1rTMode=0; Status=6; return true
  2. Checkesnec1L_Internal @ 0x1403a4d60 -> jmp to a code cave
  3. cave                  @ 0x1403a52d0 -> Version=5; clear tags; insert the 7
                                              LC_* feature tags; Status=6;
                                              Isla1rTMode=0; return 0
  4. DLLEvaluation         @ 0x1403a6f00 -> evalPassed=1; return true

The cave lives in the (now-dead) tail of Checkesnec1L_Internal, which is safe to
overwrite: every static branch target into it comes from inside that same
function (bypassed by the entry jmp), and no data pointer references it. The next
real function starts at 0x1403a5408, well past the cave's end.

All RIP-relative / call / jmp displacements are computed from absolute VAs.
The PE OptionalHeader checksum is recomputed afterwards so the file stays valid.
"""
import os
import shutil
import struct

SRC = "extracted/app/LightBurn.exe"
DST = "cracked/LightBurn.exe"

# .text: VA 0x140001000 maps to file offset 0x400 (verified against raw bytes).
TEXT_VA = 0x140001000
TEXT_ROFF = 0x400


def roff(va):
    return TEXT_ROFF + (va - TEXT_VA)


# ---- license-manager globals (reldnaHesnec1L::*) ----
ISLA1RT_MODE = 0x1411d18fd   # bool (byte)  "is trial mode"
EVAL_PASSED = 0x1411d18fe    # bool (byte)  DLL-integrity result
STATUS = 0x1411d1900         # int          license state (6 = fully licensed)
VERSION = 0x14122bf28        # int          edition level (5 = LC_DESIGN, top)
TAGS = 0x14122bf68           # QSet<QString> feature/hardware tags

# The 7 feature tags to insert. Each is a global QString object that already
# holds the hex-encoded word the feature gates compare against (see NOTES 16c).
LC_TAGS = [
    ("boss", 0x14122bf40),     # LC_BOSS   626f7373
    ("fiber", 0x14122bf48),    # LC_FIBER  6669626572  (galvo)
    ("gcode", 0x14122bf60),    # LC_GCODE  67636f6465
    ("term", 0x14122bf50),     # LC_TERM   7465726d
    ("lotus", 0x14122bf38),    # LC_LOTUS  6c6f747573
    ("omtech", 0x14122bf58),   # LC_OMTECH 6f6d74656368
    ("thunder", 0x14122c0a8),  # LC_THUNDER 7468756e646572
]

CLEAR = 0x140164370          # QSet<QString>::clear(this)
INSERT = 0x1400cc0f0         # QSet<QString>::insert(this, iter_out*, value*)

ALLOW_ENTRY = 0x1403a22f0
CHECK_ENTRY = 0x1403a4d60
CAVE = 0x1403a52d0
DLLEVAL = 0x1403a6f00
NEXT_FN_AFTER_CAVE = 0x1403a5408


def u32(x):
    return struct.pack("<I", x & 0xFFFFFFFF)


class Asm:
    """Tiny x86-64 emitter that tracks the running VA for displacement math."""

    def __init__(self, base):
        self.b = bytearray()
        self.va = base

    def _emit(self, *parts):
        for p in parts:
            if isinstance(p, int):
                self.b.append(p)
            else:
                self.b += p

    @staticmethod
    def _rip(start, length, target):
        return (target - (start + length)) & 0xFFFFFFFF

    # mov BYTE [rip+disp], imm8          C6 05 disp32 imm8
    def movb_rip_imm8(self, target, imm):
        s = self.va
        self._emit(0xC6, 0x05, u32(self._rip(s, 7, target)), imm & 0xFF)
        self.va += 7

    # mov DWORD [rip+disp], imm32        C7 05 disp32 imm32
    def movl_rip_imm32(self, target, imm):
        s = self.va
        self._emit(0xC7, 0x05, u32(self._rip(s, 10, target)), u32(imm))
        self.va += 10

    # lea rcx, [rip+disp]                48 8D 0D disp32
    def lea_rcx_rip(self, target):
        s = self.va
        self._emit(0x48, 0x8D, 0x0D, u32(self._rip(s, 7, target)))
        self.va += 7

    # lea r8, [rip+disp]                 4C 8D 05 disp32
    def lea_r8_rip(self, target):
        s = self.va
        self._emit(0x4C, 0x8D, 0x05, u32(self._rip(s, 7, target)))
        self.va += 7

    # lea rdx, [rsp+8]                   48 8D 54 24 08
    def lea_rdx_rsp8(self):
        self._emit(0x48, 0x8D, 0x54, 0x24, 0x08)
        self.va += 5

    # call rel32                         E8 disp32
    def call_rel(self, target):
        s = self.va
        self._emit(0xE8, u32((target - (s + 5)) & 0xFFFFFFFF))
        self.va += 5

    # jmp rel32                          E9 disp32
    def jmp_rel(self, target):
        s = self.va
        self._emit(0xE9, u32((target - (s + 5)) & 0xFFFFFFFF))
        self.va += 5

    def sub_rsp16(self):   # 48 83 EC 10
        self._emit(0x48, 0x83, 0xEC, 0x10)
        self.va += 4

    def add_rsp16(self):   # 48 83 C4 10
        self._emit(0x48, 0x83, 0xC4, 0x10)
        self.va += 4

    def xor_eax(self):     # 31 C0
        self._emit(0x31, 0xC0)
        self.va += 2

    def mov_eax1(self):    # B8 01 00 00 00
        self._emit(0xB8, u32(1))
        self.va += 5

    def ret(self):         # C3
        self._emit(0xC3)
        self.va += 1

    def bytes(self):
        return bytes(self.b)


def build_allow():
    a = Asm(ALLOW_ENTRY)
    a.movb_rip_imm8(ISLA1RT_MODE, 0)   # Isla1rTMode = false
    a.movl_rip_imm32(STATUS, 6)        # Status = fully licensed
    a.mov_eax1()                       # return true
    a.ret()
    return a.bytes()


def build_check_entry():
    a = Asm(CHECK_ENTRY)
    a.jmp_rel(CAVE)                    # skip the whole original body
    return a.bytes()


def build_cave():
    a = Asm(CAVE)
    a.sub_rsp16()                      # 16-byte frame; keeps rsp%16==0 for calls
    a.movl_rip_imm32(VERSION, 5)       # Version = LC_DESIGN (top edition)
    a.movl_rip_imm32(STATUS, 6)        # Status = fully licensed
    a.movb_rip_imm8(ISLA1RT_MODE, 0)   # Isla1rTMode = false
    a.lea_rcx_rip(TAGS)                # clear(&tags)
    a.call_rel(CLEAR)
    for _name, lc in LC_TAGS:          # tags.insert(LC_i) for each feature tag
        a.lea_r8_rip(lc)               #   r8 = &LC_i (QString* value)
        a.lea_rdx_rsp8()               #   rdx = 8-byte iterator out slot
        a.lea_rcx_rip(TAGS)            #   rcx = &tags
        a.call_rel(INSERT)
    a.xor_eax()                        # return 0 (success)
    a.add_rsp16()
    a.ret()
    return a.bytes()


def build_dlleval():
    a = Asm(DLLEVAL)
    a.movb_rip_imm8(EVAL_PASSED, 1)    # evalPassed = true
    a.mov_eax1()                       # return true
    a.ret()
    return a.bytes()


def recompute_pe_checksum(data):
    """Return (new_data, old_sum, new_sum). Sets OptionalHeader.CheckSum."""
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off + 4] != b"PE\0\0":
        raise ValueError("not a PE file")
    # Optional header starts at pe_off + 24 (size of COFF header).
    opt_off = pe_off + 24
    magic = struct.unpack_from("<H", data, opt_off)[0]
    # CheckSum is at offset 64 from the start of the optional header for both
    # PE32 (0x10B) and PE32+ (0x110)... actually it's a fixed field: for PE32+
    # the optional header layout puts CheckSum at opt_off + 0x98? No -- the
    # CheckSum field is at a constant offset from the optional-header start:
    #   PE32 : 0x40 ; PE32+ : 0x5C  ... but both are "after" the standard fields.
    # Simplest robust approach: the CheckSum field is at opt_off + (0x5C if PE32+ else 0x40).
    cs_off = opt_off + (0x5C if magic == 0x20B else 0x40)
    old_sum = struct.unpack_from("<I", data, cs_off)[0]

    buf = bytearray(data)
    struct.pack_into("<I", buf, cs_off, 0)
    total = len(buf)
    n = len(buf)
    for i in range(0, n - 1, 2):
        total += (buf[i] | (buf[i + 1] << 8)) & 0xFFFF
    if n & 1:
        total += buf[n - 1] & 0xFF
    total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    total &= 0xFFFF
    struct.pack_into("<I", buf, cs_off, total)
    return bytes(buf), old_sum, total


def main():
    os.makedirs("cracked", exist_ok=True)
    shutil.copyfile(SRC, DST)
    data = bytearray(open(DST, "rb").read())

    patches = [
        ("Allow entry", ALLOW_ENTRY, build_allow()),
        ("Checkesnec1L_Internal entry (jmp)", CHECK_ENTRY, build_check_entry()),
        ("cave", CAVE, build_cave()),
        ("DLLEvaluation entry", DLLEVAL, build_dlleval()),
    ]

    cave = build_cave()
    cave_end = CAVE + len(cave)
    assert cave_end <= NEXT_FN_AFTER_CAVE, \
        f"cave overruns next function: {cave_end:#x} > {NEXT_FN_AFTER_CAVE:#x}"

    for label, va, blob in patches:
        off = roff(va)
        assert 0 <= off and off + len(blob) <= len(data), f"out of range: {va:#x}"
        data[off:off + len(blob)] = blob
        print(f"patched {label:38s} {va:#012x} +{len(blob):3d}B @ file_off {off:#08x}")

    print(f"cave spans {CAVE:#x}..{cave_end:#x}  (next fn {NEXT_FN_AFTER_CAVE:#x})")

    data = bytearray(recompute_pe_checksum(bytes(data))[0])
    open(DST, "wb").write(data)
    print("OK ->", DST)


if __name__ == "__main__":
    main()
