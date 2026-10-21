# SYNERGY AI WORKSPACE V0.6 Integration Runtime

Built on V0.5. Original vendored AVITO project remains untouched. No claim of real publisher integration.

## What changed
- `workspace/integration_v06.py`: CRM → original AVITO LeadScorer / imported original AUTOPILOT SMMAgent → review task → approved action → local sandbox receipt → audit.
- `POST /v1/workflows/lead-plan`: accepts `{lead_id, kind, request}`. Supported kinds: `avito.message`, `avito.listing_update`, `smm.post`, `smm.message`. SMM branch *requires the actual original Python source* at `vendor/python-runtime/src/agi_autopilot/agents/smm.py`.
- `POST /v1/actions/{id}/simulate`: only after approval; returns `NOT_SENT` and logs a local audit entry. **Never sends external requests.**
- Desktop buttons to prepare CRM-linked AI drafts and perform an approved local simulation.
- 16 Python unit tests on this build, including 5 new workflow tests.

## Run
```bash
python -m unittest discover -s tests -v
python -m workspace.service
```
Then run Desktop from `desktop`: `npm install && npm run dev`. For Tauri build inspect existing build_windows.bat and install Rust, Node and required Windows toolchain.

## Provenance, status and restrictions
- Included: original user-uploaded AI-AVITO in `vendor/avito_ai_combine`.
- Not included: original GitHub SMM HTML/JS/CSS and original AUTOPILOT integration Rust/Tauri source / Python source, which must be imported via `import_original_sources.py` and `sync_smm_native.py`.
- Imported SMM cabinets remain isolated in sandboxed iframe. There is *no direct JS-to-CRM bridge* yet.
- Import the actual source and review it before embedding; iframe sandbox restricts direct same-origin access, but original scripts still need a security audit before any production deployment.
- External providers, real Avito sends, OAuth, live API secrets, Windows EXE and live desktop E2E are **not verified**. Simulator is intentionally local-only.
- The local API token is a single bearer token for prototype usage, **not** production-grade OIDC/RBAC/MFA.
