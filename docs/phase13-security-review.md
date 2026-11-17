# Phase 13 synthetic prototype: engineering security review

Status: internal engineering review of the draft, not an independent assessment or production approval. Scope is the Phase 13 prototype and its dependency on the unmerged Phase 12 identity draft. All fixtures and data are synthetic.

## Controls exercised in automated tests

- Current server-side membership and role are rechecked for protected intake operations; two tenant-bound test applications reject each other's document access.
- Uploads have file, batch and per-tenant document-count bounds. Known quota rejections remove their temporary source; uncertain database outcomes retain it for offline reconciliation.
- Stored files are checked for regular-file identity when opened and their SHA-256 is rechecked before processing and review promotion. This does not make storage immutable.
- Worker claims have hashed tokens, a bounded lease and retry count; concurrent workers and version updates are tested against a disposable PostgreSQL database.
- Parser subprocesses have timeouts and OS resource limits, with different controls on Linux and Windows. Malformed, encrypted and unsupported PDF cases have synthetic tests.
- A quiesced synthetic backup/restore and app/database restart test covers the source, extracted result and approved review evidence. Authenticated operations fail closed during a simulated database outage.

## Findings that remain open

1. **Identity and transport:** the application is still a localhost synthetic prototype using HTTP and non-Secure cookies. Browser OIDC sign-in, approved certificate deployment, MFA and an independent identity/security review remain outstanding. Two same-host QA applications use separate programmatic cookie jars; simultaneous browser sessions on that host are not verified.
2. **Tenant boundary:** application checks depend on verified sessions and one database role. There is no database row-level security, separate tenant credentials, or protection against a privileged database or storage operator.
3. **Storage and availability:** the source directory must be private and controlled. Hard links, parent-directory replacement, privileged modifications, and changes after a successful hash check are not fully prevented. The document count is not a filesystem disk quota or rate limit. Unknown commit outcomes can leave orphan files; inventory is offline and does not automatically repair or delete them.
4. **Parsing:** resource limits are not a sandbox, and OS limits differ by platform. Parser libraries may have vulnerabilities; untrusted production documents, active content analysis and image-only OCR are outside this prototype's validated scope. Four exact bundled synthetic PDF fixtures have explicitly hash-allowlisted lenient parsing variants.
5. **Operations and recovery:** backups require coordinated pause of writes and separate backup of database and source files. Automated retention, encryption at rest, distributed worker supervision, monitoring and recovery objectives are not established. Test backups are temporary.
6. **Audit and lifecycle:** local review events are hash-linked but can be rewritten by a privileged database user. Independent audit storage, retention policy, deletion controls and governance approval are not implemented.

The draft must remain synthetic-only until these controls are designed, independently reviewed and tested for the intended environment. Passing CI is evidence for the tested cases, not a certification.

