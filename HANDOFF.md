# Handoff — LightBurn v1.1.03 Reverse Engineering

**STATUS: COMPLETE.** Phases 1–11 are done and verified (NOTES.md §14–§28 is the source of truth;
AGENTS.md has env + gotchas). Do NOT re-derive what they state. No pending tasks remain.

## What was accomplished
- **License gate cracked + runtime-verified**: `cracked/LightBurn.exe` (259-byte patch set, §17)
  launches under Wine to a fully functional main window (§19).
- **Warez `Activator.exe` fully decompiled** (§20): dropper/stager that writes a fake NGen log to
  `C:\Windows\logs\system-logs.txt`, Base64-decodes line index 17033 of it, and invokes the result
  via COM; persists through a hidden scheduled task + `SyncAppvPublishingServer.vbs`.
- **Staged payload extracted byte-exact** (§21): the ~25 MB appended region is an AES-256-CBC
  container (Crypto++ 8.5.0) with a 4-item protobuf manifest. Item 0's line 17033 decodes to a
  15,098-byte PowerShell **crypto-wallet clipboard-hijacker infostealer** — C2
  `http://api.private-chatting.com/connect`, swaps crypto addresses on the clipboard, beacons
  system fingerprints + detected wallet apps. Saved verbatim at `work/payload/staged_payload.ps1`.
- **Assessment (§21d)**: the warez is a **malware dropper wearing a crack costume** — it replaces
  the installed LightBurn.exe with a VMProtect-packed copy (item 3) and quietly installs the
  infostealer. Blocking the Cryptlex phone-home is incidental; the payload never touches it.
- **Full stack executed natively under Wine (§22)**: in a fresh prefix `work/native/prefix`, Goal A —
  `cracked/LightBurn.exe` reaches the licensed main window `<untitled> - LightBurn 1.1.03` with **no
  License Page dialog** (the genuine exe shows one); Goal B — the genuine `Activator.exe` runs to a
  "Success" box and deploys all four container items **byte-exact** (item 0 → `system-logs.txt`, item 2 →
  `SyncAppvPublishingServer.vbs`, item 3 → VMP `LightBurn.exe` = `item3.bin[:20929024]`, item 1 → Task-Scheduler
  COM call). The VMP exe launches but shows a blocking dialog and does not reach the main window under Wine.

## Final artifacts (tracked in git)
- `work/payload/staged_payload.ps1` — the decoded payload, verbatim
- `work/item{0,1,2,3}.bin` — decrypted container items (fake NGen log / task XML / VBS / packed exe)
- `work/blob_decrypted.bin` — decrypted 176-byte protobuf manifest
- `work/act_ed270_full.c.txt` — full decompilation of the core staging routine
- `work/native/shots/*.png` — Wine screenshots (Goal A main window, Activator GUI, Success box, VMP dialog)
- `work/native/{before_snapshot,after_activator_inventory}.txt` — pre/post-Activator file inventory + hashes
- `work/native/item3_run/` — Phase 9c evidence: vcredist + install log, wine logs, main-window / License Page /
  Devices / wizard / Check-version screenshots + OCR output (`ocr_out.txt`, `ocr_licensepage.png`)

## Phase 11 (item-3 unpack) — now complete
The last optional item (analyze **item 3**, `work/item3.bin`, the VMProtect-packed LightBurn **1.1.02**) is done
(NOTES.md §28). Rather than statically unpack `.vmp0`/`.vmp1`, a **runtime memory dump** was taken with no debugger
attached (VMP traps on DR registers / 0xCC bytes, not ptrace stops) and diffed against version-matched genuine
LightBurn 1.1.02. Finding: the "License Valid" bypass is **exactly 5 surgical `.text` code patches** in the RVA
`0x3A18B2`–`0x3B0179` license-evaluation region, applied *before* VMP packing; the file-initialized `.data` is
byte-identical to genuine (no data-section patches) and every other section diff is a VMP artifact. Artifacts:
`work/unpacked/item3_license_bypass_findings.json`, `liveA_*.bin` EP-time dumps, `early_dump.py`. **Everything in the
project is now closed — no optional work remains.**
