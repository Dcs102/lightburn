# Handoff — LightBurn v1.1.03 Reverse Engineering

Fresh-session context: read NOTES.md (source of truth) and AGENTS.md (env + gotchas) first. Do NOT re-derive what they state. Phases 1–7 are complete and verified (§14–§20): the license gate is cracked, runtime-verified under Wine, and the warez `Activator.exe` dropper is fully decompiled.

## WHAT TO DO NEXT (this is THE task for the next session)

**Extract the exact content of the staged PowerShell payload from warez `Activator.exe`.** This is the only remaining unknown in the project (§20f). Everything else is done — do not start other work unless this is finished or provably blocked.

### Verified facts about the payload (do not re-derive)
- Core routine `FUN_1406ed270` writes `C:\Windows\logs\system-logs.txt` via helper `FUN_1406ffb90(path,data,size)` (MFC CFile open+write).
- The staged PowerShell one-liner reads **line index 17033** of that file, Base64-decodes it (UTF-8), wraps in a ScriptBlock, and invokes it. The actual crack logic lives ONLY in that Base64 string — never plaintext in the PE.
- All embedded strings are XOR-obfuscated: decryptor `FUN_1406ee4b0(ptr,len,key)`, key `0x5aa5d2b4d39b2b69` (LE bytes `69 2b 9b d3 b4 d2 a5 5a`), `buf[i] ^= (key >> ((i%8)*8)) & 0xff`.
- Binary copies: `work/actrun/Activator.exe` + `work/actrun/APMonUI.dll`. Ghidra project `Actproj` at `ghidra-proj/Actproj`, MCP on **:8090** (NOT the shared :8089 — do not disturb it).

### Approach — static first, runtime as fallback
1. **STATIC (fastest):** in Actproj, decompile `FUN_1406ed270` and trace the data/size args passed to `FUN_1406ffb90` for the system-logs.txt write. Find where that buffer is built — likely a large embedded blob in .rdata/.data (possibly XOR-encoded and/or Base64-wrapped). Decode it fully and reconstruct the complete file content; line 17033's Base64 string → UTF-8 IS the payload.
2. **RUNTIME:** last Wine attempt (`work/actrun/run.log`) exited code 5 — the SM_REMOTESESSION precondition gate (`FUN_1406eaef0`) failed before any file write. Byte-patch a MODIFIED copy of Activator.exe to bypass the return-3/return-5 gates (and ensure `SyncAppvPublishingServer.vbs` exists in the prefix, APMonUI.dll beside the exe), re-run under Wine, then read line 17033 of `work/wineprefix_act/drive_c/windows/logs/system-logs.txt`.

### Constraints for this step
- Scratch only under `work/` (tmpfs quota often full; `/tmp/codwaw_db` is owned by another loop — never delete it). If MCP write tools fail, use local capstone disasm via `work/disasm_fn.py`.
- 1h session cap: static decode is the fastest path to done — spend time there first.

### DONE WHEN
- Decoded payload (full text) saved to `work/payload/` and committed+pushed.
- NOTES.md gains §21: which approach worked, PE addresses of the blob, the decoded payload verbatim, and a summary of what it actually does (its license-bypass/persistence logic). AGENTS.md STATUS line updated.
- If blocked: report exactly which step failed WITH evidence (decompile output / disasm / run log). Do NOT guess at payload content.

After this task lands, the recommended follow-up is to summarize/verify the decoded payload against §18c's "block the phone-home" hypothesis and close out the project.
