# SYNERGY AI WORKSPACE V0.7 — Provider Runtime (offline safe baseline)

## New
- `GET /v1/providers`: provider capability inventory and explicit NOT_VERIFIED status.
- `GET /v1/sources`: immutable-by-content SHA256 report of present original source files.
- `POST /v1/actions/{id}/provider-dry-run`: operator-labelled, approval-gated provider simulation with request_id idempotency and SQLite audit receipt. Does **not** use network.
- Real provider execution remains disabled, including after approval.
- All original AI-AVITO files retained. SMM + AUTOPILOT repository imports need GitHub access (`python import_original_sources.py`; `python sync_smm_native.py`). Source inventory makes absence explicit.

### Example sandbox request
`POST /v1/actions/1/provider-dry-run` with bearer token and JSON `{"provider":"avito","operator":"test-operator","request_id":"test-001"}` after action approval.

## Verification
`python -m unittest discover -s tests -v`

## Not yet accomplished
No verified OAuth session, production credentials, real provider writes, network E2E, native Windows EXE or Tauri GUI automation. A source hash is not an upstream signature or licensing verification. Do not use real customer data in test calls.
