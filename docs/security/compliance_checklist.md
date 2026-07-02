# Aegis — Offline-First Compliance Checklist

This checklist supports certification claims for air-gapped, offline-first enterprise
deployments. Map each item to your applicable standard (ISO 27001, NIST SP 800-53,
NIS2, GDPR Art. 25/32).

---

## ✅ Authentication & Access Control

- [x] Local authentication only — no external IdP, no OAuth/SAML to cloud
- [x] Password hashed with Argon2id (OWASP recommended)
- [x] Account lockout after 5 consecutive failures
- [x] JWT tokens signed with HS256; secret ≥ 256 bits
- [x] Server-side session revocation (token hash stored in DB)
- [x] Session expiry: configurable, default 60 minutes
- [x] RBAC with 4 built-in roles (superadmin, admin, operator, viewer)
- [x] Granular permissions (22 permission types across 8 resource domains)
- [x] Default superadmin credentials flagged at startup; must be changed

## ✅ Data Protection

- [x] Encryption at rest: AES-256-GCM for all sensitive data
- [x] Key material never stored in database or logs
- [x] Keystore encrypted with PBKDF2-HMAC-SHA256 (600,000 iterations)
- [x] Key rotation supported (`POST /security/keys/rotate`)
- [x] Backup archives encrypted (AES-256-GCM, `.aeb` format)
- [x] Backup passphrase independent from keystore passphrase
- [x] Database file permission: 0640 (owner read/write, group read)
- [x] Keystore file permission: 0600 (owner read/write only)

## ✅ Integrity

- [x] Model files registered with SHA-256 fingerprint
- [x] Model integrity verified before inference (optional startup check)
- [x] Audit log rows chained with HMAC-SHA256 (tamper-evident)
- [x] Chain verification method available (`AuditReader.verify_chain()`)

## ✅ Audit & Non-Repudiation

- [x] All authentication events logged (success, failure, lockout)
- [x] All authorization denials logged
- [x] All privileged actions logged (key rotation, role changes, backup)
- [x] Audit log is append-only (no UPDATE/DELETE operations)
- [x] Each audit row contains: timestamp, actor, resource, action, outcome, IP
- [x] Audit log queryable with time range, actor, and resource filters
- [x] Audit read access restricted to `audit:read` permission

## ✅ Air-Gap / Offline-First

- [x] Zero HTTP calls to external services (no telemetry, no analytics, no CDN)
- [x] No automatic model downloads
- [x] All Python dependencies installable from local wheelhouse
- [x] No cloud IdP (local JWT only)
- [x] No external key management service (local keystore only)
- [x] All logs written to local rotating files only
- [x] Backup archives designed for offline transport (encrypted local files)

## ✅ Hardening

- [x] Process runs as non-root dedicated user
- [x] Systemd unit hardening documented (`ProtectSystem`, `NoNewPrivileges`, etc.)
- [x] Network binding to localhost only (no public interface)
- [x] Disk encryption (LUKS2) documented as mandatory prerequisite
- [x] File permissions documented and enforced
- [x] Secure Boot integration documented (optional, TPM 2.0)

## ⚠️ Items Requiring Operational Controls

- [ ] Dual-person integrity for superadmin actions (procedural, not technical)
- [ ] Hardware security key (FIDO2/YubiKey) for superadmin (future enhancement)
- [ ] Network-level air-gap enforcement (firewall/iptables — OS layer, out of scope)
- [ ] Log export to SIEM (optional, offline export only — future enhancement)
- [ ] Certificate-based mTLS between Admin Studio and backend (future enhancement)

---

## Mapping to Standards

| Control | ISO 27001 | NIST SP 800-53 | GDPR |
|---|---|---|---|
| Argon2id password hashing | A.9.4.3 | IA-5 | Art. 32 |
| AES-256-GCM encryption | A.10.1.1 | SC-28 | Art. 32 |
| RBAC | A.9.1, A.9.2 | AC-2, AC-3 | Art. 25 |
| Audit log | A.12.4 | AU-2, AU-9 | Art. 30 |
| Session management | A.9.4.2 | AC-12 | Art. 32 |
| Key rotation | A.10.1.2 | SC-12 | Art. 32 |
| Model integrity | A.12.5.1 | SI-7 | — |
| Backup encryption | A.12.3 | CP-9 | Art. 32 |
