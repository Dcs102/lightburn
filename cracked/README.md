# LightBurn 1.1.03 — Cracked

A fully-licensed, all-features build of LightBurn v1.1.03 (x64). Only
`LightBurn.exe` is modified; every other file in this folder is byte-identical to
the stock app (`../extracted/app/`).

## What was changed

Four surgical patches inside `LightBurn.exe` (see `../NOTES.md` §17 and the
reproducible patcher `../work/patch_license.py`):

| # | Function (entry)            | Effect |
|---|-----------------------------|--------|
| 1 | `Allow` @ `0x1403a22f0`     | Force `Isla1rTMode=0`, `Status=6` (full license), return true. |
| 2 | `Checkesnec1L_Internal` @ `0x1403a4d60` | `jmp` to a code cave that sets `Version=5`, `Status=6`, `Isla1rTMode=0`, clears the feature-tag set, then inserts all seven LC_* tags (BOSS, FIBER, GCODE, TERM, LOTUS, OMTECH, THUNDER). |
| 3 | code cave @ `0x1403a52d0`   | The 218-byte shellcode above (reuses the app's own Qt `QSet::clear`/`insert`). |
| 4 | `DLLEvaluation` @ `0x1403a6f00` | Force `evalPassed=1`, return true. |

Result: the app reports a full license, no trial countdown, and every
feature/edition gate (BOSS / Fiber / G-Code / Term / Lotus / OmTech / Thunder) is
enabled — with no activation dialog, no network check, and no `LexActivator.dll`
dependency.

## How to run

This folder is a complete, self-contained app directory. Run `LightBurn.exe`
directly (Windows x64). To deploy elsewhere, copy the whole folder, or just drop
the patched `LightBurn.exe` over the one in any stock LightBurn install.

## Reproduce

```sh
cd ..            # repo root
python3 work/patch_license.py     # reads extracted/app/LightBurn.exe -> cracked/LightBurn.exe
```

The patcher rewrites only 259 bytes total and recomputes the PE checksum, so the
resulting binary is a valid PE.
