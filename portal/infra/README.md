# Deployment assets

The verified default is a local Docker Compose stack: non-root API/web,
PostgreSQL, persistent evidence/database volumes, private data ports and Nginx
bound to 127.0.0.1:8080. No external infrastructure is provisioned by these files.

The production override adds a Caddy TLS gateway and switches the application to
OIDC, disables demo seeding and requires deployment configuration. It has not been
validated against a real domain, IdP or cloud environment. It is not an AWS
Terraform implementation or a sovereignty certification.

Before using it: configure the trusted issuer/client/callback, provision exact
subjects, start with clean reviewed data volumes, choose a supported secret/key
mechanism, review storage encryption, IAM/network access, telemetry/retention,
backups/restore, distributed rate limits and incident ownership. Use the security
guide and docs/implementation/02_OPERATIONS_AND_LIMITS.md as acceptance checklists.
Do not reuse local demo credentials as production credentials.

Cloud-specific IaC and managed service adapters remain explicit extensions after
the deployment profile, account, region, cost and service-location rules are known.
