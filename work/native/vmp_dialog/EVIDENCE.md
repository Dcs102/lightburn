# Phase 9b — item-3 (VMP) LightBurn.exe dialog: exact text + classification

## Verbatim dialog text (captured, not guessed)

Title bar: `LightBurn.exe`
Message (single multi-line string, standard Windows PE-loader error format):

    The procedure entry point ?PPLParallelForEventGuid@Concurrency@@3U_GUID@@B
    could not be located in the dynamic link library CONCRT140.dll.

Button: `OK`  (a single-button modal #32770 dialog; dismissing it terminates the process)

## Which API produced it

The Windows/Wine **PE module loader's "missing entry point" failure path**, displayed via
`MessageBoxW` (standard `#32770` dialog class + a `Button`, as seen in the wine log). This is the
canonical message emitted when the loader cannot resolve a hard import: it fills in the imported
symbol name and the DLL it was expected to come from. It is NOT an app-authored string, NOT a
VMProtect anti-VM/anti-debug message, and NOT a license error.

## Method that worked (and why the others did not)

1. **Preload shim (hook.c / hook.so) — FAILED to intercept.** Built a 64-bit .so wrapping
   MessageBoxW/A, TaskDialogIndirect, DrawTextW/ExtTextOutW/TextOutW + a GetTickCount canary,
   loaded via `LD_PRELOAD`. The constructor fired (shim loaded into the wine process) but NO hook
   ever ran — not even the GetTickCount canary. Conclusion: ELF symbol interposition does NOT catch
   Wine PE imports; Wine fills the IAT with direct pointers resolved by its own loader, bypassing
   the dynamic linker. So a preload .so cannot wrap Win32 API calls from a PE. (Kept hook.c/hook.so
   as evidence of the attempt.)
2. **High-DPI render + OCR — WORKED.** Set `HKCU\Control Panel\Desktop\LogPixels=192` (200%) in the
   prefix user.reg, relaunched item3; the dialog rendered at 704x204 (exactly 2x the native 352x102).
   Moved it fully on-screen with xdotool, captured the full scene with `spectacle -f -b -n`
   (screenshot = X root = 3440x1440, scale 1:1), cropped to the window bbox, and OCR'd with
   rapidocr-onnxruntime. Native-res (352x102) OCR also read it once upscaled 3x. Both agree.
3. **Static cross-check — CONFIRMED.** item3.bin's static import table lists only
   `?_GetNumberOfVirtualProcessors@...` from CONCRT140.dll (VMP strips the table to ~1 import/DLL and
   reconstructs the full original table at runtime). The genuine LightBurn.exe hard-imports 18
   CONCRT140 symbols including this one. Wine's concrt140.dll (prefix system32 AND builtin, 278
   exports) HAS `?_GetNumberOfVirtualProcessors@...` but has NO `PPLParallelForEventGuid` export at
   all -> the symbol is genuinely missing from Wine's Concurrency Runtime.

## Classification: MISSING DEPENDENCY (Wine environment gap)

- The VMP-packed item3 requires the PPL (Parallel Patterns Library) export
  `?PPLParallelForEventGuid@Concurrency@@3U_GUID@@B` from CONCRT140.dll (Microsoft Concurrency
  Runtime 14.0, part of the VC++ 2015-2022 redistributable) at load time.
- Wine's built-in concrt140.dll is incomplete and does not export it -> the loader aborts module
  load with the "procedure entry point ... could not be located" MessageBox before any app code runs.
- NOT anti-VM, NOT anti-debug, NOT a license check. It is purely that Wine's concrt140 lacks one PPL
  symbol the binary needs.

## Why the genuine exe runs but item3 does not (same symbol)

The genuine 1.1.03 LightBurn.exe ALSO hard-imports this exact symbol, yet it loads fine under Wine
(reaches the code-46 "License System Error" WMI dialog, §19/§22b). Wine's loader is lenient for a
normally-loaded main module: it leaves the one unresolvable IAT slot NULL and continues (the PPL code
path is not reached during startup). The VMP packer, by contrast, reconstructs/re-resolves the full
original import table at runtime in a way that forces strict resolution of every symbol, so the single
missing PPL export becomes a fatal load error. Net effect: identical dependency gap, but only the VMP
build trips it hard under Wine.

## Implication for real Windows

On real Windows, CONCRT140.dll (from the VC++ 2015-2022 redistributable, which LightBurn ships as
vcredist_2017_x64.exe) DOES export `PPLParallelForEventGuid`. The import resolves, the module loads,
and item3 runs normally. So this dialog is a **Wine-only limitation**, not evidence that the warez
payload is broken on real Windows. (To run item3 under Wine one would need to supply a complete
concrt140.dll — e.g. copy the real Microsoft one into the prefix system32.)

## Files in this directory
- hook.c / hook.so / hook.log : preload-shim attempt + its (empty-of-calls) log
- cap_ocr.py : window-move + spectacle-capture + rapidocr helper
- run_hook.sh : shim launch script
- hidpi_full.png : 200%-DPI dialog crop (784x284, dialog at 40,40 size 704x204)
- dlg_x2.png / dlg_x3.png : autocontrast upscaled dialog crops (cleanest OCR input)
- native_full.png / native_x3.png : native-res (352x102) crop + 3x upscale
- evidence_hidpi_fullscreen.png : full 3440x1440 scene at capture time
- wine_hi.log / wine_genuine_now.log : wine stderr for the item3 and genuine runs
