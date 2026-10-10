# AGENTS.md — LightBurn 1.1.03 Reverse Engineering

Target: **LightBurn v1.1.03** laser-engraver software (x64 package, but the binary is a **32-bit i386 PE**, image base `0x400000`).

## What's loaded
- Ghidra MCP headless server: `http://127.0.0.1:8089` (systemd user svc `ghidra-mcp-headless`, v7.0.0)
- **A second MCP instance runs at `http://127.0.0.1:8090`** (started ad hoc for the Activator work;
  launcher `/home/Dcs102/tools/ghidra-mcp/start-headless.sh` honors `GHIDRA_MCP_PORT`). Use it to avoid
  disturbing the shared `:8089` program. Pass `program=Activator.exe` explicitly on every call.
- **Three Ghidra projects exist:**
  - The original installer project (`LightBurn-v1.1.03.exe`, i386 Inno Setup stub, 2,550 fns).
  - **`LBproj`** at `/var/home/Dcs102/lightburn/ghidra-proj/LBproj` — the REAL app binaries
    (`LightBurn.exe` x64 = 59,632 fns, `LexActivator.dll`, `DoCheck64.exe`), all auto-analyzed.
    This is where the license gate lives (see NOTES.md §14).
  - **`Actproj`** at `/var/home/Dcs102/lightburn/ghidra-proj/Actproj` — the warez dropper
    `Activator.exe` (PE32+ x86-64, 99,672 fns), auto-analyzed. See NOTES.md §20.
- To work on the app: `POST /open_project {"path":".../LBproj.gpr"}` then
  `POST /load_program_from_project {"path":"/LightBurn.exe"}`. Then use the `ghidra_*` tools.
- Source binaries (extracted): `/var/home/Dcs102/lightburn/extracted/app/` (clean paths).
- Original download: `/var/home/Dcs102/lightburn/LightBurn 1.1.03 (x64) Multilingual/`
  (also contains `crack.zip` → `Activator.exe`, `APMonUI.dll`, `readme.txt`). **Verified** via the
  complete 1.1.02 sibling torrent (see NOTES.md §18): crack.zip is a ZIP of those three files; the
  warez strategy = block Cryptlex phone-home (`api.cryptlex.com`). NOTE: the 1.1.03 torrent's own
  `crack.zip` + installer are **corrupted (~75% zeroed, unusable)** — use the 1.1.02 copy for genuine content.

## Gotchas (verified — do NOT re-derive)
- The PE **entry point is zeroed** (`AddressOfEntryPoint = 0`): no WinMain will be found by name.
  Find the real entry via `.edata` export table, TLS callbacks, or by locating the biggest
  call-graph cluster in `.text`.
- `load_program` with explicit `language`/`compiler_spec` params forces **Raw Binary** loading
  (no PE parse). Omit those params to get auto-detect → proper PE loader.
- `import_file` does NOT work headless ("requires GUI mode"). Use `load_program`.
- File paths with spaces break the server's file resolution — always use the clean
  `/var/home/Dcs102/lightburn/bin/` copy.
- After deleting/recreating a project dir, Ghidra may complain "Unable to lock project"
  (stale lock); `rm -rf` the `LightBurn` + `LightBurn.gpr/.rep` dirs before recreating.
- **This Ghidra build is STRIPPED — `Features/Script` is absent**, so the `GhidraScript` class
  does not exist and standard Java postScripts will NOT compile ("cannot find symbol: class
  GhidraScript"). Use the MCP REST tools, or plain non-GhidraScript classes.
- `analyzeHeadless` needs `JAVA_HOME` set explicitly; background jobs are killed on shell-tool
  timeout (process-group kill) → launch with `setsid ... < /dev/null & disown`.
- **JDK ignores `TMPDIR`** — to keep Ghidra's temp/DB-buffer files off the quota-limited `/tmp`, pass
  `-Djava.io.tmpdir=<real-disk-dir>` explicitly: via `JAVA_OPTS` for the MCP launcher
  (`start-headless.sh`) and via `GHIDRA_JAVA_OPTIONS` for `analyzeHeadless`. Used
  `work/act_tmp` for the Activator analysis (NOTES.md §20).
- objdump `--start-address/--stop-address` is unreliable for these PEs; dump full disasm + grep/sed.
- **tmpfs quota (user `Dcs102`) = 12,449 MB, shared across `/tmp`,`/dev/shm`,`/run/user/1000`.**
  It gets driven to 100% by the parallel CoDWaW loop's `/tmp/codwaw_db` (~12 GB). When full: the
  Ghidra MCP server's WRITE tools fail (`read_memory` EOFException, decompile "Disk quota exceeded",
  some stored fn bodies read back corrupted/UNKNOWN) and ANY write to `/tmp` fails. **Do NOT delete
  `/tmp/codwaw_db`** (another active loop owns it). Workaround: local capstone disasm via
  `work/disasm_fn.py` (PE section map + VA→file offset; image base `0x140000000`, .text roff `0x400`),
  and put scratch under `/var/home/Dcs102/lightburn/work/` (NOT `/tmp`). Ghidra READ tools mostly
  still work while quota is full.
- **Wine runtime testing:** use Proton wine 11.0 at
  `/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine`,
  prefix `/var/home/Dcs102/lightburn/work/wineprefix`. Host X `:0` is headless Wayland — root-window
  capture is all-black; capture per-window instead: `DISPLAY=:0 import -window <id> out.png`.
  Dismiss modal dialogs with `xdotool windowactivate --sync <id>` + `xdotool key Return`.
  Under Wine the app shows a "License System Error" dialog (code 46, WMI fingerprint — Wine stubs
  WMI) before the main window; that's a Wine artifact, NOT a crack defect (see NOTES.md §19).

## Useful endpoints (REST at :8089, same as MCP tools)
- Project mgmt: `POST /open_project {"path":"<.gpr or dir>"}`, `POST /load_program_from_project
  {"path":"/LightBurn.exe"}`, `GET /list_projects`, `POST /close_project`. (Params come from the
  JSON **body**, not query string.)
- `GET /get_function_count`, `GET /list_functions_enhanced?offset=&limit=`
- `GET /decompile_function?address=0x...`  (or `POST /force_decompile`)
- `GET /search_functions?name_pattern=...`, `GET /list_strings?filter=...`
- `GET /list_imports`, `GET /list_exports`, `GET /list_segments`
- `POST /reanalyze` (full auto-analysis pass)

## Task context
Goal: decompile/understand LightBurn's behavior. The `.text` entropy (~6.4) indicates mostly
plain MSVC code, not a heavy packer — standard decompilation should yield readable C.

**STATUS (Phase 9 complete — project closed out):** the license gate is cracked AND runtime-verified, and the
full warez stack was executed natively under Wine (no VM/QEMU) in a fresh prefix `work/native/prefix`
(NOTES.md §22). **Goal A:** `cracked/LightBurn.exe` (259-byte patch set: Allow / Checkesnec1L_Internal+code-cave
/ DLLEvaluation, see NOTES.md §17) launches under Wine to the licensed main window `<untitled> - LightBurn 1.1.03`
with **no "License Page" dialog** (the genuine exe shows one) — re-confirms §19. **Goal B:** the genuine
`Activator.exe` runs end-to-end, shows a "Success" box, and deploys all four container items **byte-exact**
(item 0 → `C:\Windows\logs\system-logs.txt`, item 2 → `SyncAppvPublishingServer.vbs`, item 3 → VMP-packed
`LightBurn.exe` = `item3.bin[:20929024]`, item 1 → Task-Scheduler COM call); the VMP exe launches but shows a
blocking dialog and does not reach the main window under Wine (§22d). The warez `Activator.exe`
is fully decompiled (NOTES.md §20) **and its embedded container is fully extracted** (NOTES.md §21): the ~25 MB
appended region is an AES-256-CBC container (key/IV in a 48-byte descriptor at file offset `0xd5e818`; Crypto++
8.5.0) whose protobuf manifest lists 4 items — item 0 = the staged fake-NGen-log `system-logs.txt` (line index
17033 Base64-decodes to a **15,098-byte PowerShell crypto-wallet clipboard-hijacker infostealer**, C2
`api.private-chatting.com`), item 1 = Task-Scheduler XML, item 2 = `SyncAppvPublishingServer.vbs`, item 3 = a
VMProtect-packed replacement LightBurn.exe. The warez is a malware dropper wearing a crack costume (§21d).
**Final artifacts (tracked):** `work/payload/staged_payload.ps1` (decoded payload, verbatim) +
`work/item{0,1,2,3}.bin` (decrypted container items), plus `work/blob_decrypted.bin` (manifest) and
`work/act_ed270_full.c.txt`. Phase 9 added `work/native/shots/*.png` (Wine screenshots) +
`work/native/{before_snapshot,after_activator_inventory}.txt`. **Phase 9b** read the item-3 (VMP) dialog verbatim
(NOTES.md §23): it is the PE-loader "missing entry point" error — `The procedure entry point
?PPLParallelForEventGuid@Concurrency@@3U_GUID@@B could not be located in the dynamic link library CONCRT140.dll` —
i.e. a **missing dependency** (Wine's concrt140 lacks that PPL export), NOT anti-VM/license; evidence in
`work/native/vmp_dialog/`. Only optional work left: unpack item 3 to locate its license bypass. NOTES.md is the
source of truth; do not re-derive what it says.
