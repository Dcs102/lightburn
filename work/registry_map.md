# Registry & prefs.ini map for LightBurn.exe (Phase 10, Task 2)

Target: `LightBurn.exe` (PE32+, image base `0x140000000`), Ghidra LBproj @ :8089.
Scope: every Windows-registry path the exe reads/writes, plus any INI (prefs.ini) key access.

## Summary

- **Windows registry** — exactly two mechanisms, both fully enumerated below:
  1. **File-association keys** under `HKCU` (set by `LB_SetFileAssociation`).
  2. **LexActivator "csetz" data store** under `SOFTWARE\CLASSES\csetz` (HKCU or HKLM), used by the
     Cryptlex client for its local license data.
- **prefs.ini** — LightBurn does **NOT** use the Win32 INI APIs (`GetPrivateProfile*` /
  `WritePrivateProfile*` are not imported at all). It uses **Qt's `QSettings`** (own INI parser) over
  three INI files. So there are no `GetPrivateProfileName` call sites to enumerate; the settings keys
  live in Qt-scoped INI sections, not the registry.

## 1. Registry API surface (complete — verified against ADVAPI32 import table)

ADVAPI32 registry imports: `RegOpenKeyExW`, `RegQueryValueExW`, `RegSetValueExW`, `RegCreateKeyExW`,
`RegDeleteKeyW`, `RegCloseKey`, `RegGetValueW`. (Other ADVAPI32 imports — `Crypt*`, service APIs,
`GetUserNameW` — are not registry.) All 7 registry APIs are used by exactly **4 helper functions**:

| Helper @ VA | Win32 calls | Behavior |
|---|---|---|
| `RegSet(HKEY, key, value)` @ `0x1403ae980` | `RegGetValueW` (idempotency check) + `RegCreateKeyExW` + `RegSetValueExW` | sets the **default value** (`L""`, REG_SZ) of `key`; skips write if already correct |
| `RegDelete(HKEY, subkey)` @ `0x1403ae8e0` | `RegDeleteKeyW` | deletes a subkey tree (logs "removed old user association") |
| `LexActivator::ReadFromRegistry(value, buf, type, isRoot)` @ `0x1404d5830` | `RegOpenKeyExW` + `RegQueryValueExW` | reads value under fixed path `SOFTWARE\CLASSES\csetz` |
| `LexActivator::WriteToRegistry(value, data, len, isRoot)` @ `0x1404d5c90` | `RegOpenKeyExW` + `RegCreateKeyExW` + `RegSetValueExW` | writes REG_SZ value under fixed path `SOFTWARE\CLASSES\csetz` |

The HKEY in the csetz helpers is computed as `(HKEY)(isRoot - 0x7fffffff)`:
`isRoot=false → 0x80000001 = HKCU`, `isRoot=true → 0x80000002 = HKLM`.

## 2. File-association keys — all under `HKCU` (HKEY_CURRENT_USER)

Set by `LB_SetFileAssociation` @ `0x1403ac320` (called at startup to register `.lbrn`/`.lbrn2`).
String literals decoded from `.rdata` (`0x14095b8b0`–`0x14095be10`). `RegSet` writes the **default value**;
the final `Command` value is the full path to `LightBurn.exe` (built at runtime, `/`→`\`).

| # | Op | Key path (under HKCU) | Value | Purpose |
|---|---|---|---|---|
| 1 | DELETE | `Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.lbrn\UserChoice` | — | clear Windows "open with" user choice for `.lbrn` |
| 2 | DELETE | `Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.lbrn2\UserChoice` | — | same for `.lbrn2` |
| 3 | SET (default) | `Software\Classes\.lbrn` | `LightBurn.LightBurn.1` | map `.lbrn` extension → prog id |
| 4 | SET (default) | `Software\Classes\.lbrn2` | `LightBurn.LightBurn.1` | map `.lbrn2` extension → prog id |
| 5 | SET (default) | `Software\Classes\.lbrn\Content Type` | `text/plain` | MIME content type |
| 6 | SET (default) | `Software\Classes\.lbrn\PerceivedType` | `text` | Windows perceived file type |
| 7 | SET (default) | `Software\Classes\.lbrn2\Content Type` | `text/plain` | MIME content type |
| 8 | SET (default) | `Software\Classes\.lbrn2\PerceivedType` | `text` | Windows perceived file type |
| 9 | SET (default) | `Software\Classes\.lbrn\OpenWithProgIds\LightBurn.LightBurn.1` | `` (empty) | register prog id in OpenWith list |
| 10 | SET (default) | `Software\Classes\.lbrn2\OpenWithProgIds\LightBurn.LightBurn.1` | `` (empty) | register prog id in OpenWith list |
| 11 | SET (default) | `Software\Classes\LightBurn.LightBurn.1` | `LightBurn` | friendly name for the prog id |
| 12 | SET (default) | `Software\Classes\LightBurn.LightBurn.1\Shell\Open\Command` | `<full path to LightBurn.exe>` | "Open" verb command line |

After any change it calls `SHChangeNotify(SHCNE_ASSOCCHANGED)` to refresh the shell.

## 3. LexActivator "csetz" data store (HKCU or HKLM)

The Cryptlex client's local license-data store. Reached via
`LexDataStore::GetValue/SaveValue` → `ReadFromSystemStorage/WriteToSystemStorage` →
`ReadFromRegistry/WriteToRegistry`.

- **Path:** `SOFTWARE\CLASSES\csetz` — stored hex-obfuscated as the literal
  `"534F4654574152455C434C41535345535C637365747A"`, HexDecode + toUTF16'd at first use (thread-local static).
- **HKEY:** `HKLM` if `LexDataStore::IsRoot` (`?IsRoot@LexDataStore@LexActivator@@2_NA` @ `0x14123cd89`,
  set when running elevated) else `HKCU`. Normal (non-admin) runs → **HKCU**.
- **Value names:** `<key>` + `SHA256(<key>)` (full hex digest; only the first char if a *floating*
  license). Computed by `LexDataStore::GetKeySuffix` @ `0x1404c7f20`. Names are therefore opaque/derived.
- **Values:** encrypted at rest (`LexDecrypter`/`LexWrapDecrypter` on read; the literal `"EXCEPTION"` is
  the error sentinel). In-memory `CacheStore` map fronts the registry.
- **Callers:** 23 `GetValue`/`SaveValue` sites across the LexActivator activation/validation flow
  (`0x1404bf9ad`…`0x1404e4bff`). Representative keys observed:
  - `ProductId` → value `"ESHFCE"` (a "license key has been set" flag; written by `SetyeKesnec1L` @ `0x1404c2030`)
  - `yeKesnec1L` → the license key itself
  - plus other Cryptlex data-store keys (activation metadata, etc.) read/written in the same flow.
- **Purpose:** persist Cryptlex activation state / license key / product metadata locally so the client
  can validate offline and re-sync with the server.

## 4. prefs.ini — Qt `QSettings` INI files (NOT Win32 INI API)

- **No** `GetPrivateProfileString/Int/Section/Struct` or `WritePrivateProfile*` symbols are imported
  (verified against the import table) → there are **no `GetPrivateProfileName` call sites**.
- LightBurn uses Qt's `QSettings` (INI format, own parser) over three files, paths relative to the app
  directory:

| File | String @ VA | Role |
|---|---|---|
| `/prefs.ini` | `0x14090f098` | main user preferences |
| `/defaultprefs.ini` | `0x14090f0a8` | factory-default preferences (template) |
| `/licenseprefs.ini` | `0x14090f7f0` | license-related preferences |

Individual setting keys are Qt-scoped INI sections accessed via `QSettings::value()/setValue()`, so they
are not enumerable as Win32 API call sites; they do not touch the Windows registry.
