# SYNERGY AI WORKSPACE

Unified desktop integration of SYNERGY AI AUTOPILOT, AI-SMM and AI-AVITO.

> **Status: release-candidate integration in progress.** Windows installation, native GUI E2E, live OAuth and provider execution are not yet verified.

## Authoritative sources

- [AUTOPILOT Rust/Tauri integration](https://github.com/Shtenco/synergy_agi_autopilot/tree/integration/synergy-ai-autopilot-v1)
- [AUTOPILOT Python capabilities](https://github.com/Shtenco/synergy_agi_autopilot/tree/feat/capability-runtime-v1)
- [AI-SMM original UI](https://github.com/Shtenco/synergy.github.io/tree/main/smm)
- AI-AVITO original code: provided separately in `AVITO_AI_COMBINE_V1_BUSINESS_AUTOPILOT(1).zip`; DO NOT upload live credentials or personal datasets.

## Safety and release gates

External sending is disabled by default. Require authenticated operator approval, platform-specific API authorization, idempotency and audit evidence before any real external side effects. Source presence is not sufficient to claim a working integration.

The RC branch should contain the complete sanitized source tree and reproducible Windows CI; do not publish a release until the installer and desktop E2E checks are verified.
