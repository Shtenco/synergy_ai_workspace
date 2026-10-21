# SYNERGY AI WORKSPACE V0.3 — verified local adapter layer

## Actual integrations
- Original user-provided `vendor/avito_ai_combine` retained. API `POST /v1/avito/score` imports and invokes **the original** `vendor.avito_ai_combine.crm.scoring.LeadScorer` (offline, no Avito credentials). Results are explicitly candidates, not verified buyers.
- `GET /v1/integrations` reports actual source paths and availability for every named SMM cabinet and the Python/Rust AUTOPILOT branches. Missing code reports `available:false`, never 'connected'.
- `POST /v1/autopilot/smm/plan` calls the **original** `SMMAgent.content_plan()` from `vendor/python-runtime` if imported; returns HTTP 409 if unavailable. Never publishes.
- Tauri frontend now exposes an offline AVITO scoring button and a guarded original SMM agent action, in addition to tasks, CRM and audit.
- Every adapter call records a local audit event without duplicating customer data.

## Source import
Run `python import_original_sources.py` on a GitHub-connected machine. This imports specific real branches:
- `Shtenco/synergy_agi_autopilot` → `integration/synergy-ai-autopilot-v1` (`vendor/desktop-integration`) and `feat/capability-runtime-v1` (`vendor/python-runtime`)
- `Shtenco/synergy.github.io` → `vendor/synergy.github.io` (`smm/`)
- `Shtenco/synergy_lead_search_engline` → `vendor/synergy_lead_search_engline`

Existing source files are preserved; remote network was not available in this build environment. The SMM HTML cabinets have not yet been embedded, Rust/Tauri desktop has not been compiled, AVITO API authentication and network calls are not performed. No false claim of complete E2E coverage.

## Validate
`python -m unittest discover -s tests -v`

## Run
1. `python -m workspace.service`
2. In `desktop`: `npm install` and `npm run tauri dev` (Rust and Tauri prereqs required).
3. Paste printed local token into GUI.
4. Use AVITO original local scoring, tasks, CRM, audit; AUTOPILOT SMM planning after import.

## Security note
Local bearer token is a development session, **not** OIDC/MFA/RBAC. No external writes are enabled; no OAuth tokens collected; do not expose HTTP service on public interfaces. Production requires trusted origin controls, session lifecycle, application packaging and extensive integration testing.
