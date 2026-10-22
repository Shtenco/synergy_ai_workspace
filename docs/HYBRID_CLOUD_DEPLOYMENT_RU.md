# SYNERGY Hybrid Cloud Google + Oracle

**Status: deployment preparation only. No cloud VM, DNS or cloud authentication verified.**

## Roles
- Github Pages: public marketing/tutorial UI; do not expose secrets.
- Oracle VM: existing local single-operator Workspace, SQLite and task/financial ledger, bound to 127.0.0.1:8129 only.
- Google Cloud Run/Vertex AI: private inference service using IAM workload identity, not browser API keys.
- Cross-cloud communication: only through authenticated private transport; future OIDC/MFA and multi-tenant RLS required before production launch.

## OCI preflight
1. Confirm instance exists and is authorized; inventory its region, shape, architecture and disk.
2. Confirm OCI network ACL and OS firewall deny public inbound 8129 and 5432.
3. Checkout branch release/v1.0-desktop-rc on the owner's instance in a private folder using an authorized GitHub identity.
4. Run unit tests (capital_engine and meta_orchestrator). Use a restricted env file for SYNERGY_TOKEN and a persistent volume for SYNERGY_DB.
5. Start workspace.service; verify 127.0.0.1:8129 only, via authorized SSH port forwarding.
6. Verify WAL backup, restore, least-privilege OS user and monitoring.

## GCP preflight
1. Confirm project ID, region, service accounts, billing caps, Vertex AI API availability.
2. Deploy reviewed code as a private Cloud Run service (do NOT allow unauthenticated).
3. Service-to-service auth: short-lived identity tokens, verify issuer/audience, deny all unapproved callers.
4. No client-side credentials. Control egress, max instances, request size, costs and logs.
5. AI tasks must be policy-filtered and asynchronous when necessary, never automatically trading or sending payments.

## Authentication architecture
The existing workspace.service uses one local bearer token and is **not a safe public multi-tenant service**. Do NOT expose it over reverse proxy without implementing OIDC/MFA, tenant-scoped DB, RBAC, audit and CSRF controls. The current bridge is read-only and cannot be used as a general execution bus.

## Readiness checklist
- [ ] OCI machine is reachable and owner-authorized
- [ ] SSH private tunnel works, public port 8129 unreachable
- [ ] Workspace tests pass on target architecture
- [ ] Backup/restore verified
- [ ] Google project, IAM and billing verified
- [ ] Cloud Run private endpoint deployed and unauthenticated calls denied
- [ ] Secure cross-cloud identity established and tested
- [ ] Tenant isolation and policy checks complete before customer data
