# LightBurn v1.1.03 Reverse Engineering

Reverse-engineering project targeting **LightBurn v1.1.03** (laser-engraver software),
with the goal of understanding and cracking its Cryptlex-based licensing/activation gate.

## Layout

- `AGENTS.md` — environment setup, Ghidra MCP endpoints, verified gotchas (read first)
- `NOTES.md` — running findings doc; **the source of truth**
- `HANDOFF.md` — paste-in prompt to resume the task in a fresh session
- `bin/` — clean-path copies of binaries for tooling (paths with spaces break Ghidra MCP)
- `extracted/app/` — extracted app (Inno Setup payload): `LightBurn.exe`, `LexActivator.dll`,
  `DoCheck64.exe`, Qt5/OpenSSL DLLs
- `ghidra-proj/` — Ghidra project (`LBproj`) holding the analyzed app binaries *(gitignored)*

## Key facts (verified)

- Licensing = **Cryptlex SDK** (`LexActivator.dll`); embedded product/key credentials;
  API `https://api.cryptlex.com/v3/activations`. License TYPE gates DSP/galvo hardware.
- `LightBurn.exe` is a stripped x86-64 Qt5 C++ binary (base `0x140000000`).
- Ghidra MCP headless server at `http://127.0.0.1:8089` (systemd user svc `ghidra-mcp-headless`).

See `NOTES.md` for full detail.
