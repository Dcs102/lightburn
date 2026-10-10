# Handoff — LightBurn v1.1.03 Reverse Engineering

**STATUS: COMPLETE.** Phases 1–8 are done and verified (NOTES.md §14–§21 is the source of truth;
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

## Final artifacts (tracked in git)
- `work/payload/staged_payload.ps1` — the decoded payload, verbatim
- `work/item{0,1,2,3}.bin` — decrypted container items (fake NGen log / task XML / VBS / packed exe)
- `work/blob_decrypted.bin` — decrypted 176-byte protobuf manifest
- `work/act_ed270_full.c.txt` — full decompilation of the core staging routine

## Only remaining optional work
Analyze **item 3** (`work/item3.bin`, the VMProtect-packed LightBurn.exe, PE32+ imagebase
`0x20000001000`) to confirm where its license bypass lives. VMP packing hides the modification —
expect to need unpacking/analysis of `.vmp0`/`.vmp1` or dynamic analysis under Wine. Everything
else in the project is closed.
