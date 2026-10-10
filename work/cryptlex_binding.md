# Cryptlex / LexActivator export binding in LightBurn.exe (Phase 10, Task 1)

Target: `LightBurn.exe` (PE32+, image base `0x140000000`, 59,632 fns), Ghidra LBproj @ :8089.
Question: where are the GetProcAddress call sites that resolve the 36 LexActivator/Cryptlex
exports, where do the function pointers land, and what is the binding mechanism?

## Conclusion (TL;DR)

**There are NO GetProcAddress call sites that resolve LexActivator.dll's 36 exports.** The Cryptlex
client is **statically linked (in-process)** into LightBurn.exe — all 36 functions' logic is compiled
directly into the exe as C++ code in the `LexActivator::` namespace. `LexActivator.dll` is referenced
**only** for an MD5 integrity check (`DLLEvaluation`); it is never `LoadLibrary`-ed and its exports are
never resolved. This **corrects the §6b hypothesis** ("references/loads `/LexActivator.dll` via
`LoadLibraryW`") — the exe only *references* the path, it does not load or bind the DLL.

The "export names are not literal strings" observation is consistent with this: they are not looked up
by name at all (no ordinal table, no manual-resolve loop) because there is no dynamic binding.

## 1. Binding mechanism = in-process static linking (evidence)

- The license-decision wrapper `FUN_1404c14b0` (the "IsLicenseValid + server sync" call used by
  `Allow()`/`Checkesnec1L_Internal`, §16b) makes **direct calls to in-process symbols**, not function
  pointers:
  - `Isesnec1LValid()` @ `0x1404c15f0` (body `0x1404c15f0..0x1404c1b14`, ~1.3 KB of real code)
  - `LexActivator::LexValidator::ValidateSuccessCode` @ `0x1404e44b0`
  - `LexActivator::LexPayloadMaps::Getno1tav1tcAPayload` (in-process)
  - `LexActivator::LexThread::InvokeServerSync` @ `0x1404e1660`
- **54** `LexActivator::` C++ template/inline functions are compiled into the binary
  (`std::vector<LexActivator::FeatureFlag>`, `std::_Tree_node<...LexActivator::Metadata...>`,
  `pair<..., LexActivator::no1tav1tcAPayload>`, etc.) — only present if the client is statically linked.
- Embedded Botan build path (the in-process crypto): `d:\a\1\s\lexactivator\Botan/botan_all_msvc_x64.cpp`
  @ `0x140fc67d8`.
- The Cryptlex namespace even contains its own `GetProcAddress` user — `LexActivator::GetWinOsVersionInfo`
  @ `0x1404d4d80` — but it resolves **`ntdll!RtlGetVersion`** (OS fingerprinting), not a LexActivator.dll
  export.

## 2. Full GetProcAddress census (47 sites) — none resolve LexActivator/Cryptlex exports

Method: `work/scan_imports.py` parses the PE import dir, locates the IAT slots for
`LoadLibraryA/W`, `GetProcAddress`, `FreeLibrary`, then scans `.text` for every indirect call
(`FF 15 <disp32>`) / direct call (`E8 <disp32>`) targeting those slots. **47** call sites total:
**40 `GetProcAddress` + 4 `LoadLibrary` (1 W + 3 A) + 3 `FreeLibrary`.**

| Containing function @ entry | Call-site VA(s) | DLL resolved | Exports resolved | Where pointers land |
|---|---|---|---|---|
| `CameraCap::LoadCameraLibrary` @ `0x140211da0` | `LoadLibraryW` `0x140211e8a`; `GetProcAddress` ×29 `0x140211eb8`…`0x14021229c` | a camera-capture DLL loaded from `<appdir>\<name>.dll` (HMODULE → `DAT_14120a0a8`) | 29 × `CAP_*` (`CAP_InitCaptureLib`, `CAP_GetDeviceList`, …, `CAP_TakePhoto`) | globals `DAT_141209fc0`…`DAT_14120a0a0` (one per export) |
| `LB_LinkTimerFunctions` @ `0x1403ac200` | `LoadLibraryA` `0x1403ac20b`; `GetProcAddress` ×2 `0x1403ac227`,`0x1403ac242`; `FreeLibrary` `0x1403ac760` | `winmm.dll` | `timeBeginPeriod`, `timeEndPeriod` | local/static ptrs |
| `LexActivator::GetWinOsVersionInfo` @ `0x1404d4d80` | `GetProcAddress` `0x1404d4e3b` | `ntdll.dll` (via `GetModuleHandleA`) | `RtlGetVersion` | local `pFVar12` |
| `Curl_load_library` @ `0x14055dc00` | `LoadLibraryA` ×2 `0x14055dc78`,`0x14055dd83`; `GetProcAddress` ×3 `0x14055dc39`,`0x14055dc9d`,`0x14055de41` | libcurl runtime deps (`ws2_32`, `wldap32`, `crypt32`, …) | assorted curl symbols | curl internal tables |
| libcurl schannel backend `FUN_14056f4b0` @ `0x14056f4b0` | `GetProcAddress` `0x14056f58a` | `ntdll.dll` (via `GetModuleHandleA`) | `wine_get_version` (Wine detection) | local `pFVar12` |
| `Curl_sspi_global_init` @ `0x140577be0` | `FreeLibrary` `0x140577bc0`; `GetProcAddress` `0x140577c38` | `secur32.dll` (SSPI) | SSPI entry points | curl `s_pSecFn` table |
| `__scrt_initialize_thread_safe_statics` @ `0x140839b90` | `GetProcAddress` ×3 `0x140839beb`,`0x140839bfe`,`0x140839c11` | CRT static-init helper | (CRT) | CRT internals |
| (misc) | `FreeLibrary` `0x140203e6a` | — | — | — |

**None of the 47 sites resolves a LexActivator.dll / Cryptlex export.** The only place LightBurn uses
the classic "load DLL → GetProcAddress into global function-pointer slots" pattern is the **camera**
library (`CAP_*` → `DAT_141209fc0..DAT_14120a0a8`) — a useful contrast: that IS dynamic binding, Cryptlex
is NOT.

## 3. Why LexActivator.dll is not dynamically bound (exhaustive)

- **Not a static import.** The exe's 37 imported DLLs are: SHELL32, potrace, SETUPAPI, libusb-1.0,
  WS2_32, Qt5{MultimediaWidgets,PrintSupport,Widgets,Multimedia,Gui,SerialPort,Network,Xml,Core},
  MSVCP140, dbghelp, ADVAPI32, USER32, WINHTTP, CRYPT32, IPHLPAPI, ole32, OLEAUT32, CONCRT140, KERNEL32,
  VCRUNTIME140, and the `api-ms-win-crt-*` UCRT set. **No LexActivator.dll.**
- **No delay-load imports.** PE data directory 13 (DelayImport) is absent (only dirs 0,1,2,3,4,5,6,9,10,12
  are present).
- **Not among the 4 `LoadLibrary` calls** in the binary: camera (`LoadLibraryW`, `0x140211e8a`),
  winmm (`LoadLibraryA`, `0x1403ac20b`), and two libcurl deps (`LoadLibraryA`, `0x14055dc78`/`0x14055dd83`).
- **Only reference** to the DLL is the path string `/LexActivator.dll` @ `0x14095cbd0`, consumed solely by
  `DLLEvaluation` (below).

## 4. Where the 36 functions actually live (in-process symbols, not pointers)

The 36 LexActivator.dll exports (§6a) have in-process equivalents compiled into LightBurn.exe. Key
decision-path addresses:

| LexActivator.dll export | In-process equivalent @ VA | Notes |
|---|---|---|
| `IsLicenseValid` | `Isesnec1LValid` @ `0x1404c15f0` | called by `FUN_1404c14b0` |
| (success-code check) | `LexValidator::ValidateSuccessCode` @ `0x1404e44b0` | |
| (server sync) | `LexThread::InvokeServerSync` @ `0x1404e1660` | |
| `GetCustomField` | `GetCustomField` @ `0x1403a8070` | "version"/"tags" fields (§16c) |
| (activation payload) | `LexPayloadMaps::Getno1tav1tcAPayload` | in-process |
| …(remaining 30) | `LexActivator::` namespace fns | ~54 template/inline + core classes |

There are **no global function-pointer slots** for these — they are ordinary code addresses called
directly. The license-state globals they read/write are the `reldnaHesnec1L::*` fields (§14b):
`Status` `0x1411d1900`, `evalPassed` `0x1411d18fe`, `Isla1rTMode` `0x1411d18fd`, `Version` `0x14122bf28`,
`tags` `0x14122bf68`.

## 5. LexActivator.dll's actual role: an MD5 integrity canary

`DLLEvaluation` @ `0x1403a6f00` (decompiled):
1. Builds path = `QCoreApplication::applicationDirPath() + "/LexActivator.dll"` (string @ `0x14095cbd0`).
2. Opens it as a **`QFile`** (file read — NOT `LoadLibrary`), reads in `0x800`-byte chunks into a
   `QCryptographicHash` (MD5, ctor arg 1).
3. Compares the 16-byte MD5 to the hardcoded digest at `_DAT_1411d58e8` / `_DAT_1411d58f0`.
4. Sets `reldnaHesnec1L::evalPassed = (match)` @ `0x1411d18fe`.

So the on-disk `LexActivator.dll` is a **tamper canary**: it need not be functionally used by LightBurn.exe;
it only has to be *present and byte-identical* for `evalPassed` to be true (which gates the licensed path,
§14e). Replacing/patching the DLL trips the check — which is exactly why the §17 crack also patches
`DLLEvaluation` to force `evalPassed=1`.

## 6. Implication for the crack

Because the client is in-process, patching LightBurn.exe's license logic (the §17 patch set:
`Allow`/`Checkesnec1L_Internal`/`DLLEvaluation`) is self-sufficient — there is no external DLL whose
exports must be satisfied or stubbed. The only on-disk dependency is that `LexActivator.dll` exists and
matches the MD5 (or `DLLEvaluation` is patched, as in §17). No IAT/function-pointer redirection of the
36 exports is possible or necessary, because none exist.
