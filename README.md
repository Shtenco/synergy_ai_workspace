# SYNERGY AI WORKSPACE • integration foundation V0.1

This is an **integration shell** using the original user-provided Avito archive without altering its contents (except removal of transient `__pycache__` on packaging). It provides navigation, launches the real Avito desktop GUI in a separate process, detects imported SMM HTML pages, and checks the AUTOPILOT local API health endpoint. It does **not** claim to contain or run the full Tauri desktop or original SMM assets until imported.

## Windows quickstart

1. Install Python 3.11+, Git, and dependencies `python -m pip install -r requirements.txt`.
2. Run `python import_original_sources.py` with access to GitHub to import **original sources** for SMM, AUTOPILOT and Lead OS, including two distinct feature branch worktrees.
3. Run `start_windows.bat`.
4. For the original Rust/Tauri app, see `vendor/desktop-integration/apps/desktop` and its project-specific build tooling; it is not compiled by this package.

## Sources

- AUTOPILOT Desktop Rust/Tauri: https://github.com/Shtenco/synergy_agi_autopilot/tree/integration/synergy-ai-autopilot-v1
- AUTOPILOT Python: https://github.com/Shtenco/synergy_agi_autopilot/tree/feat/capability-runtime-v1
- SMM UI: https://github.com/Shtenco/synergy.github.io/tree/main/smm
- Lead OS: https://github.com/Shtenco/synergy_lead_search_engline
- Avito: the user-supplied `AVITO_AI_COMBINE_V1_BUSINESS_AUTOPILOT(1).zip`.

## Limitations

This is NOT the final unified Tauri EXE. SMM HTML pages open in the default browser after import, and the original Avito Tk desktop opens as a separate window. Runtime API health verification is read-only. No credentials are bundled. No automatic posting, messaging or paid promotions are enabled by this shell.
