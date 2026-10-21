# SYNERGY AI WORKSPACE V0.5 — Native Modules

This is an incremental upgrade on V0.4. **No unverified external calls.**

## What is real
- Retains the user-provided original AI-AVITO Python source in `vendor/avito_ai_combine` and local scoring adapter.
- Keeps existing SQLite CRM, task review, action approvals, audit, and fail-closed send/publish behavior.
- New **SMM Native Cabinets** tab loads the **original** upstream SMM HTML, JS and CSS (once imported) in a sandboxed iframe. This does not simulate those applications.
- The original Python `SMMAgent` is invoked via the separate imported `feat/capability-runtime-v1` branch. No invented substitute on missing source.
- Adds SHA256 per-file provenance for copied SMM source files.

## Required sources and Windows build
1. `python import_original_sources.py` (network + git; fetches original AUTOPILOT refs and SMM repository).
2. `python sync_smm_native.py` (copies original SMM assets, hashes each original file).
3. `python -m unittest discover -s tests -v` (from project root).
4. `python -m workspace.service` then enter the session token into Desktop.
5. `cd desktop && npm install && npm run tauri build` (requires Rust, Cargo, Node, Windows SDK/WebView2). `build_windows.bat` is included but ensure step 1–2 first.

## Restrictions
The original SMM pages are loaded in a sandboxed iframe **without** `allow-same-origin`, intentionally isolating cookies, privileged Tauri APIs and the token. Some upstream capabilities may be restricted. Original upstream pages may attempt network requests: do not enter live platform credentials before auditing the individual pages and securing their external endpoints. Browsing the module is not evidence of a verified live integration.

The real `integration/synergy-ai-autopilot-v1` original Desktop source remains a separate preserved vendor worktree, not silently merged over this project's Desktop frontend. Reconciliation/merging is pending.

## Acceptance evidence
Unit tests exercise action approval and verify that no unaudited network send can run. Offline E2E is API-level; Tauri executable and Windows GUI E2E cannot be claimed until built and run on Windows. Do not expose local API to LAN or the public Internet.
