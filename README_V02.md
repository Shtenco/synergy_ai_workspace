# SYNERGY AI WORKSPACE v0.2 — Tauri unified desktop skeleton

## Delivered and verified

- One React/Tauri UI with navigation: Overview, AI AUTOPILOT, AI SMM, AI AVITO, Tasks, CRM, Audit.
- Local-only Python HTTP control plane `workspace/service.py` (port 8129, binds 127.0.0.1).
- Session-token bearer authorization (token printed on startup; stored in desktop UI memory, never in localStorage).
- SQLite WAL tasks, CRM contacts, append-audit events and guarded task transitions.
- Original user-provided AI-AVITO Python source preserved under `vendor/avito_ai_combine` without alterations.
- Non-destructive importer for original GitHub repositories and AUTOPILOT feature refs: `import_original_sources.py`.
- Rust/Tauri source for Windows build under `desktop/`.

## Not delivered (not to be misrepresented)

- The original GitHub Desktop and SMM files are **not bundled** because outbound git clone in this runtime fails DNS resolution. Run the importer with network access.
- The Tauri frontend is a newly built unified shell, *not yet patched directly into* `integration/synergy-ai-autopilot-v1/apps/desktop`.
- SMM screens and AVITO Tk GUI are not yet embedded inside Tauri; their original source is preserved and an integration/status surface is provided.
- No automatic model calls, social posting, Avito publishing or external task execution is enabled. An `approved` record is **not an authorization to run externally**.
- Windows EXE not compiled here: this environment has no Cargo/Rust and network access is blocked. A build script is included.
- Local bearer auth is a single-session development control, not organization OIDC/RBAC/MFA or production security.

## Run Windows local service

Requirements: Python 3.11+ and Node.js 20+, Rust/Cargo and Tauri Windows build prerequisites for EXE. Python server itself needs standard library only.

Open `start_control_plane_windows.bat` in the folder; the console will print a session token.

## Run desktop in development

```
cd desktop
npm install
npm run tauri dev
```

Paste the token from the console into **Local API authorization**.

## Build Windows EXE (on Windows machine with Rust and Tauri build tools)

Open `build_windows.bat`. The installer is typically produced under `desktop/src-tauri/target/release/bundle/nsis/`.

## Bring in original projects

```
python import_original_sources.py
```

It clones and preserves these sources into separate folders:

- `Shtenco/synergy_agi_autopilot`, feature refs `integration/synergy-ai-autopilot-v1` and `feat/capability-runtime-v1` in detached worktrees
- `Shtenco/synergy.github.io` (SMM cabinets)
- `Shtenco/synergy_lead_search_engline` (lead CRM engine)

No branch is overwritten. If sources are not present, UI reports "Import pending". To actually connect AVITO or SMM APIs, add an explicit least-privilege adapter and test against credentials with human authorization.

## Tests

```
python -m unittest discover -s tests -v
```

## Privacy

Do not publish `runtime/*.sqlite3`, API tokens, Avito credentials, personal lead exports or .env files to public GitHub. Use a local-only backend and secure secrets storage when hardening.
