# V1.0 Desktop RC: evidence ledger

## Published to this branch
- Exact upstream SMM HTML: workspaces.html, studio.html, lead-radar.html, caseflow.html
- Standalone presence validation workflow, deliberately NOT a Windows installer workflow

## Source
https://github.com/Shtenco/synergy.github.io/tree/main/smm
Original content preserved via GitHub content API. Git blob SHAs at time of import:
- workspaces.html: a121dea97f984536e8b3308ddcd11658e3dfec3d
- studio.html: b91dd4177fac7c0f60534c9a07f5de3a638acf0a
- lead-radar.html: 375d7d7419a8494e5da1b50b1db08cb627d051c5
- caseflow.html: c24815165d4a147d6c1201717cc1066980989462

## BLOCKERS — not a full application release
- Additional HTML/CSS/JS resources of the SMM pages remain to be imported.
- Complete V0.9 Tauri / React / Rust / Python workspace source is not yet present in this GitHub branch.
- AVITO local archive requires a privacy, credential and licensing review before commit.
- AUTOPILOT Python & Tauri original branches must be fetched/imported and compatibility tested.
- GitHub Actions Windows NSIS build has not run.
- Native Desktop GUI Playwright/WebDriver E2E has not run.
- Live OAuth and authorized provider writes are NOT configured or verified.

Do not mark these as completed or publish a production installer until evidence exists.

## Additional progress (2026-10-22)
Original SMM dependencies added without re-authoring: `smm26-workspace.css`, `mission-v93.js`, `studio.js`, `workspace-pro.js`, `caseflow.js`, and `assets/pages-runtime.js`. Validation script checks the four source HTML pages and all six dependencies. Local V0.9 archive Python tests: 25/25 PASS. GitHub source-validation workflow runs still fail; cause is not confirmed because CI job logs could not be retrieved. GitHub does not yet contain the full local V0.9 source tree. No Windows build or native GUI E2E evidence exists.
