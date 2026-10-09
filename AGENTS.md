# AGENTS.md — LightBurn 1.1.03 Reverse Engineering

Target: **LightBurn v1.1.03** laser-engraver software (x64 package, but the binary is a **32-bit i386 PE**, image base `0x400000`).

## What's loaded
- Ghidra MCP headless server: `http://127.0.0.1:8089` (systemd user svc `ghidra-mcp-headless`, v7.0.0)
- **Two Ghidra projects exist:**
  - The original installer project (`LightBurn-v1.1.03.exe`, i386 Inno Setup stub, 2,550 fns).
  - **`LBproj`** at `/var/home/Dcs102/lightburn/ghidra-proj/LBproj` — the REAL app binaries
    (`LightBurn.exe` x64 = 59,632 fns, `LexActivator.dll`, `DoCheck64.exe`), all auto-analyzed.
    This is where the license gate lives (see NOTES.md §14).
- To work on the app: `POST /open_project {"path":".../LBproj.gpr"}` then
  `POST /load_program_from_project {"path":"/LightBurn.exe"}`. Then use the `ghidra_*` tools.
- Source binaries (extracted): `/var/home/Dcs102/lightburn/extracted/app/` (clean paths).
- Original download: `/var/home/Dcs102/lightburn/LightBurn 1.1.03 (x64) Multilingual/`
  (also contains `crack.zip` → `Activator.exe`, `APMonUI.dll`, `readme.txt`)

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
- objdump `--start-address/--stop-address` is unreliable for these PEs; dump full disasm + grep/sed.

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
