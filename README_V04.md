# SYNERGY AI WORKSPACE v0.4 – Local orchestration

## What works (verified)
- Original AI-AVITO vendor code retained, actual LeadScorer adapter.
- SQLite leads, tasks, action drafts, operator approval, audit trail.
- Task created in `review` when preparing an action draft for a lead; approval moves linked task to `approved`.
- External execution ALWAYS responds HTTP 409 `NO_VERIFIED_PROVIDER_ADAPTER` and records `action.execute_denied`. No live Avito/SMM writes or messages.
- React/Tauri desktop includes Action Review view.

## What does NOT yet work
- Embedded original SMM cabinets (their source is not included in this bundle; use importer when GitHub access is available).
- Original Rust desktop integration (available in upstream branch; not cloned into this bundle).
- Production OAuth / multiuser auth / external API publishing / durable job queue.
- Windows EXE: not built in this environment (Rust/Cargo unavailable).
- Not a production system. Session bearer token is printed locally and must be pasted into desktop; no persisted credentials.

## Start on Windows
```powershell
cd SYNERGY_AI_WORKSPACE_V04_WORK
python -m unittest discover -s tests -v
python -m workspace.service
# separately, after Node.js installation
cd desktop
npm install
npm run dev
# for Windows Tauri install Rust + Visual Studio Build Tools + WebView2
npm run tauri build
```

## Import upstream sources (non-destructive)
Run `python import_original_sources.py` with Git network access. It checks out both `integration/synergy-ai-autopilot-v1` and `feat/capability-runtime-v1` as separate git worktrees and clones `synergy.github.io`. Existing source trees are not overwritten. Original cabinets should be bridged with an explicit, restrictive IPC contract after security review, not treated as automatically integrated just because copied.

## API
Authenticated local bearer API on `127.0.0.1:8129`:
- `POST /v1/leads`
- `POST /v1/actions/prepare` body: `{"lead_id":1,"kind":"avito.message","draft":"..."}`
- `POST /v1/actions/{id}/approve`
- `POST /v1/actions/{id}/execute` -> HTTP 409 denied, audited.
- `GET /v1/actions`, `GET /v1/audit`, tasks, integrations, health.

## Security
Approval only authorizes a reviewed draft; it never overrides integration safety policy. No real external side effect path exists. HTTP origin allowlist and loopback binding mitigate, but do not fully prevent local malware/CSRF; production requires stronger session/roles, hardening, explicit connector allowlists and E2E tests.
