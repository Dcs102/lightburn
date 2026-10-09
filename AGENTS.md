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

**STATUS (Phase 7 complete):** the license gate is cracked AND runtime-verified. `cracked/LightBurn.exe`
(259-byte patch set: Allow / Checkesnec1L_Internal+code-cave / DLLEvaluation, see NOTES.md §17) launches
under Wine to a fully functional main window (NOTES.md §19). The warez `Activator.exe` is now fully
decompiled (NOTES.md §20): it's a dropper that stages a PowerShell payload into
`C:\Windows\logs\system-logs.txt` (Base64 at line 17033) and runs it via COM, with persistence via
`SyncAppvPublishingServer.vbs` + registry. Remaining optional work: extract/decode the staged payload
content (run Activator under Wine and read that file, or XOR-decode the embedded blob). NOTES.md is the
source of truth; do not re-derive what it says.
