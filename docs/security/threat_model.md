# Aegis — Threat Model & Risk Assessment

## Scope

This document covers the **Aegis AI Platform** (Admin Studio + Client) running in an **air-gapped, offline-first** enterprise environment. No network connectivity to external services is assumed or permitted.

---

## System Boundaries

```
┌──────────────────────────────────────────────────────────┐
│  AIR-GAP BOUNDARY                                        │
│                                                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐         │
│  │ Admin UI  │  │ Client UI │  │ CLI tools │         │
│  └──────┬───┘  └──────┬───┘  └──────┬───┘         │
│           │              │              │                   │
│           └──────────────┴──────────────┘                   │
│                          │                                   │
│                  ┌──────┴──────┐                            │
│                  │ FastAPI Backend │                            │
│                  └──────┬──────┘                            │
│         ┌─────────┴─────────┐                               │
│    ┌───┴───┐  ┌───┴───┐  ┌───┴─────┐              │
│    │ SQLite  │  │Keystore │  │ models/   │              │
│    │  (data) │  │(.bin)   │  │ documents │              │
│    └────────┘  └────────┘  └──────────┘              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## STRIDE Threat Analysis

### S — Spoofing

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Credential stuffing via admin UI | Medium | High | Argon2id hashing, account lockout after 5 failures |
| Session token theft (memory/disk) | Low | High | Short-lived JWT (60 min), session revocation, token hash in DB |
| Impersonation via JWT forgery | Low | Critical | HS256 with 256-bit secret, server-side session validation |

### T — Tampering

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Model file replacement | Low | Critical | SHA-256 fingerprint registration + automatic verification |
| Audit log manipulation | Low | High | HMAC-SHA256 chained rows; chain verification detects any edit |
| DB file tampering | Low | High | File-level permission (0600), encrypted backups |
| Config file tampering | Medium | High | .env outside web root, read-only in production |

### R — Repudiation

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Deny performing privileged actions | Medium | High | Append-only audit log with HMAC chain, actor/timestamp/outcome |

### I — Information Disclosure

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Key material exposure | Low | Critical | Keys stored only in keystore.bin (0600), never in DB or logs |
| Password leak from DB | Low | High | Argon2id hash stored, plaintext never persisted |
| Log injection / sensitive data in logs | Medium | Medium | structlog structured logging; passwords/tokens never logged |
| Backup file exposure | Low | High | Backup archives AES-256-GCM encrypted (.aeb) |

### D — Denial of Service

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Brute-force login | High | Medium | Account lockout after 5 failures, Argon2id slows guessing |
| Disk exhaustion via audit log | Medium | Medium | Log rotation policy (structlog rotating sink), DuckDB analytics |
| Model file corruption | Low | High | Integrity check on every inference startup |

### E — Elevation of Privilege

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Horizontal privilege escalation | Low | High | RBAC enforced per-endpoint, permissions embedded in JWT |
| Insecure direct object reference | Medium | Medium | All endpoints validate principal's permissions before DB access |
| Role assignment abuse | Low | Critical | Only superadmin can modify roles; all changes audit-logged |

---

## Residual Risks (Accepted)

1. **Physical access** — if an attacker gains physical access to the machine, key material in `keystore.bin` is protected only by the passphrase. Disk encryption (LUKS/BitLocker) is a prerequisite for the host OS and is out of scope for this application layer.
2. **Side-channel attacks** — timing attacks on HMAC comparison are mitigated via `hmac.compare_digest`; advanced hardware side-channels are out of scope.
3. **Compromised superadmin** — a malicious superadmin can bypass all controls. Operational controls (dual-person integrity, hardware tokens) are documented in `hardening.md`.

---

## Assets & Data Classification

| Asset | Classification | Location | Protection |
|---|---|---|---|
| Model weights | Confidential | `models/` | File permissions (0640), integrity hash |
| Training data | Confidential | `data/` | File permissions, encrypted backup |
| User credentials | Secret | SQLite `users` table | Argon2id hash, never plaintext |
| JWT secret key | Secret | `.env` (never in DB) | File permissions (0600) |
| Keystore passphrase | Secret | `.env` | File permissions (0600) |
| Audit log | Restricted | SQLite `audit_logs` | HMAC chain, read-only role required |
| Session tokens | Restricted | SQLite `sessions` | SHA-256 hash stored, raw token in memory only |
