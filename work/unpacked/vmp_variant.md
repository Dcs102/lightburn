# STEP 0 — VMProtect variant identification for item 3 (`work/item3.bin`)

Date: 2026-10-10. Method: static PE/byte analysis of `work/item3.bin` (20,929,040 B container item;
deployed exe = first 20,929,024 B) + comparison against the **genuine LightBurn 1.1.02** binary
extracted from the complete 1.1.02 sibling-torrent installer (`work/lb1102/dl/.../LightBurn-v1.1.02.exe`
→ `work/unpacked/prefix1102/drive_c/lb1102/LightBurn.exe`, 19,253,176 B).

## Verdict

**Packer: VMProtect, 3.x family — "section-stripping" layout (recent 3.x; most plausibly 3.4.x/3.5.0
era, consistent with the early/mid-2022 warez release date).** Exact sub-version is NOT determinable
statically with high confidence (no plaintext version string; stub is encrypted). The variant gate is
**passed for the runtime-dump approach**: public static unpackers that target classic VMP layouts do not
reliably handle this layout, but the binary runs to a stable main window under Wine (§24b), so dumping the
live image after VMP initialization sidesteps static unpacking entirely. **Proceeding to runtime dump.**

## Evidence

### 1. Section table — VMP signature (certain)

| Section | VA | VSz | RawSz | Notes |
|---|---|---|---|---|
| .text | 0x1000 | 0x8d3f4e | **0** | virtual-only, data stripped from file |
| .rdata | 0x8d5000 | 0x8ebc38 | **0** | ditto |
| .data | 0x11c1000 | 0x111458 | **0** | ditto |
| .pdata | 0x12d3000 | 0x5883c | **0** | ditto |
| .tls | 0x132c000 | 9 | **0** | ditto |
| _RDATA | 0x132d000 | 0x7b0 | **0** | `_RDATA` name = VMP fingerprint |
| .vmp0 | 0x132e000 | 0xb27b78 | **0** | virtual-only (no file data at all) |
| .vmp1 | 0x1e56000 | 0x13f13cc | 0x13f1400 @0x400 | **all** packed data; entropy 7.987 (~8.0 = encrypted) |
| .reloc | 0x3248000 | 0xbc | 0x200 | reduced to one small block |
| .rsrc | 0x3249000 | 0x3ec6 | 0x4000 | preserved (≈ genuine size 0x3ec8) |

The exact set `.text .rdata .data .pdata .tls _RDATA .vmp0 .vmp1 .reloc .rsrc` is VMProtect-specific
(no other packer uses `_RDATA` + `.vmp0/.vmp1`). All original sections are virtual-only (RawSz=0):
VMP removed their file data and packed it into `.vmp1`.

### 2. Entry point + stub

- EP RVA `0x1eb96d2` → VA `0x141EB96D2`, **inside .vmp1** (file off `0x63ad2`).
- First bytes: `push imm32; call 0x1430b372a` then garbage — an **encrypted/obfuscated stub prologue**
  (self-decrypting; the call target at RVA `0x30b372a` is real obfuscated code: `push rcx; jmp +0xE3600; …`).
  Stub code is split across multiple .vmp1 regions (jump chains), a VMP anti-disassembly trait.

### 3. Import table stripped to ~1 symbol/DLL (confirms §23c)

42 import descriptors, **exactly one import each** (42 total): SHELL32 `CommandLineToArgvW`, potrace
`potrace_param_default`, SETUPAPI `SetupDiEnumDeviceInfo`, libusb-1.0 `libusb_get_string_descriptor_ascii`,
WS2_32, Qt5{MultimediaWidgets,PrintSupport,Widgets,Multimedia,Gui,SerialPort,Network,Xml,Core}, MSVCP140,
dbghelp, ADVAPI32, USER32, WINHTTP, CRYPT32, IPHLPAPI, ole32, OLEAUT32, CONCRT140 `?_GetNumberOfVirtualProcessors@…`,
KERNEL32, VCRUNTIME140, 10× api-ms-win-crt-*, WTSAPI32 (+ duplicate KERNEL32/USER32 descriptors).
Full table is reconstructed at runtime (why the missing-PPL-export load error was fatal under Wine, §23d).
Saved: `work/unpacked/imports_static.json`.

### 4. PE data directories — metadata relocated into .vmp1

| Dir | item3 | genuine 1.1.02 |
|---|---|---|
| Import | VA 0x1e94ce0 (in .vmp1), Sz 0x35c = 43×20B | VA 0x1193ddc, Sz 0x2f8 |
| Exception | VA 0x31ebe30 (in .vmp1), Sz **0x5b59c** (> original 0x5883c — VMP added entries for stub code) | VA 0x12d3000 (.pdata), Sz 0x5883c |
| TLS | VA 0x2faf1e0 (in .vmp1), Sz 0x30 | VA 0x101f738, Sz 0x28 |
| LoadCfg | VA 0x31ebd90 (in .vmp1), Sz 0xa0 | VA 0x101f690, Sz 0xa0 |
| IAT | VA 0x1e63000 (in .vmp1), Sz 0x300 | VA 0x8d5000 (start of .rdata), Sz 0x6f10 |
| Export | VA 0x307ff80 (in .vmp1), Sz 0x9cb — **preserved**: 93 exports, `LightBurn.exe`, FT_* serial API | VA 0x1193410, Sz 0x9cc |
| BaseReloc | VA 0x3248000 (.reloc), Sz **0xbc** (one block) | VA 0x1332000, Sz 0xc634 |
| Debug | **removed** | VA 0x101f630, Sz 0x54 (CodeView → LightBurn.pdb) |
| Security | **removed** | VA 0x125b000, Sz 0x17b8 (Authenticode signature) |

The exception directory contents are a genuine copy of the original `.pdata` (first entries:
Begin=0x1030 End=0x105d Data=0x1078b64 — RVAs into original .text), just relocated into .vmp1.

### 5. Same-build confirmation (item3 = pack of genuine 1.1.02)

- **TimeDateStamp identical**: item3 `0x6229008b` (2022-03-09 19:31:23 UTC) == genuine 1.1.02
  `0x6229008b`. VMP preserved the original build timestamp (it is NOT a VMP fingerprint).
- **Original section VAs/sizes byte-identical** to genuine 1.1.02 (.text VSz 0x8d3f4e, .rdata 0x8ebc38,
  .data 0x111458 — note these match 1.1.02, NOT 1.1.03's 0x8d4aae/0x8ebe28/0x1114b8).
- ImageBase `0x140000000` (standard x64) — **correction**: the "imagebase 0x20000001000" recorded in
  §21b/AGENTS.md is a misread of the SectionAlignment/FileAlignment DWORDs at opt+0x28 (`00 10 00 00 |
  00 02 00 00`); the actual ImageBase QWORD at opt+0x18 is `0x140000000`. Verified by raw byte read and
  `objdump -f` (start address 0x141eb96d2).

### 6. What could NOT be determined statically

- No "VMProtect"/version string anywhere in .vmp1 (stub + payload fully encrypted; the 32k "strings"
  found are random-printable noise from the ciphertext).
- TLS directory values at VA 0x2faf1e0 look obfuscated (StartAddressOfRawData = 0x142FAF2F008, out of
  image range) — presumably fixed up by the stub at runtime.
- Exact VMP sub-version: layout matches the recent-3.x "section stripping" style (virtual-only .vmp0,
  all data in .vmp1, EP in .vmp1); warez release window (early–mid 2022) → most plausibly **VMP 3.4.x or
  3.5.0**. Public unpackers of record target the classic layout (stub with raw data in .vmp0), so static
  unpacking confidence is LOW; runtime dumping confidence is HIGH (binary demonstrably runs, §24b).

## Method that will be used (since static unpacking is not reliable here)

1. Run item3 under wine+gdb in `work/native/prefix` (MS concrt140 present, §24a); break at the
   **original 1.1.02 entry point** `0x140839F2C` (RVA 0x839f2c) — reached only after VMP has finished
   unpacking + IAT reconstruction.
2. Dump all live sections → `work/unpacked/live_*.bin`.
3. Byte-diff each section against the version-matched genuine 1.1.02 reference → the modification set is
   exactly the diff (VMP artifacts vs intentional license bypass).
