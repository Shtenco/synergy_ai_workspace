# AVITO AI COMBINE V1

Standalone Avito-only AI/CRM/automation desktop core rebuilt from the SMM AI COMBINE product concepts. Production integration is designed around official Avito APIs, OAuth, webhooks and Autoload. No other social-network runtime is included.

## Offline verification
`python -m avito_ai_combine.main --check`

## Safety defaults
COPILOT is the default autonomy mode. Monetary, destructive and high-risk writes are approval-gated; AUTOPILOT has spend limits and a global kill switch. Secrets are expected to be stored through `CredentialVault` and redacted from diagnostics.

## Live Avito connection
AVITO AI COMBINE now has a real Client Credentials connection path. Keep credentials outside source code.

Windows PowerShell:
```powershell
$env:AVITO_CLIENT_ID="..."
$env:AVITO_CLIENT_SECRET="..."
python -m avito_ai_combine.main --check-live
```

The check requests an access token, calls the current account endpoint, and reports capability flags derived from granted scopes. `--check-live` exits with code 2 when credentials are not configured and code 1 when Avito rejects/fails the connection.

Messenger client includes chat/message reads, text/image send, mark-read, voice-file lookup, blacklist and webhook subscribe/unsubscribe boundaries. Endpoint versions are explicit per operation rather than globally assumed.

## Live GUI layer

The Connection page now stores Client ID in local config and Client Secret in the encrypted credential vault, runs API CHECK off the Tk main thread, resolves the Avito account and token scopes, and persists account/capability state in SQLite.

The Messages page syncs Avito chats/messages into SQLite, creates/updates CRM leads, displays the conversation and lead context side-by-side, supports guarded AI draft generation, and sends operator-approved replies through Messenger API.

A local webhook receiver can be started on `127.0.0.1:8765/avito/webhook`. Avito webhook registration requires a public HTTPS URL; expose/proxy the local receiver through infrastructure you control, put that HTTPS URL into Connection, then use SUBSCRIBE URL. Incoming webhook events are deduplicated in SQLite and projected into local messages/leads where the payload contains message data.

AI remains provider-neutral. If no AI provider is configured, the draft workflow explicitly hands off instead of fabricating an answer. Approved knowledge remains required for autonomous customer-facing facts.


## Business modules live pass
This build wires Listings, Stats, Dashboard, Autoload v4 status, Reviews, Calls, Promotion observation, persistent Automation Rules and policy-gated AI Autopilot into the Avito-only runtime. Live results depend on the scopes/capabilities granted to the connected Avito application/account. Promotion observation never spends money; monetary execution remains approval/policy gated.
