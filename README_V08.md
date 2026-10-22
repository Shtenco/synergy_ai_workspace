# SYNERGY AI WORKSPACE V0.8 Native Integration

This package **does not** contain pristine GitHub SMM/AUTOPILOT sources because direct Git cloning is blocked inside the authoring environment. The original Avito archive is preserved in `vendor/avito_ai_combine`.

## Exact, verified GitHub locations

* `Shtenco/synergy.github.io`, `main`: `smm/workspaces.html`, `smm/studio.html`, `smm/lead-radar.html`, `smm/ai-studio.html`, `smm/caseflow.html`, `smm/cabinet.html`, `smm/SMMV2/cabinet.html`
* `Shtenco/synergy_agi_autopilot`, `feat/capability-runtime-v1`: `src/agi_autopilot/agents/smm.py`, `src/agi_autopilot/runtime.py`, `src/agi_autopilot/app.py`
* `Shtenco/synergy_agi_autopilot`, `integration/synergy-ai-autopilot-v1`: `apps/desktop/src/App.tsx`, Rust/Tauri implementation.

## Get originals (requires GitHub access)

```powershell
python import_original_sources.py
python sync_smm_native.py
python verify_imports.py
python -m pytest -q tests
```

Run `start_control_plane_windows.bat`, then in another terminal:

```powershell
cd desktop
npm install
npm run tauri dev
```

To build Windows NSIS exe, install Rust, Node, Visual Studio Build Tools / WebView2 prerequisites and run `build_windows.bat`. `.github/workflows/windows-release.yml` offers a build on a hosted Windows runner once this V0.8 code is committed to a repository with Actions enabled.

## Security boundaries

* All original SMM HTML/CSS/JS copied without modification, with SHA256 manifest and byte-for-byte verification.
* Third-party SMM cabinets display in sandboxed iframe without allow-same-origin. They do **not** receive the local bearer token.
* Original AI-AVITO scoring and original imported AUTOPILOT SMM planner have local API adapters.
* External API calls remain DENIED until OAuth redirect/PKCE, scoped token storage, permissions, sandbox accounts, and official-provider API acceptance tests are completed. A provider registry is NOT an OAuth connection.
* Local CRM/task/audit + provider dry-runs are not proof of remote side effects. No external sending in this release.
* SQLite connections close on leaving transaction context after this version's fix.

## Not yet proven

Real SMM assets embedded after GitHub import, Rust/Tauri build, real browser-based GUI E2E, real official provider OAuth or Avito/Telegram/VK mutations. Windows installer is not included in this archive.
