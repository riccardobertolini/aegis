# Aegis — Compliance Checklist (Offline-First)

> Framework di riferimento: ISO/IEC 27001:2022, NIST SP 800-53 Rev.5, GDPR Art. 25 & 32.  
> Scope: sistema AI enterprise locale, air-gapped, dati esclusivamente on-premise.

---

## Legenda

| Simbolo | Significato |
|---|---|
| ✅ | Implementato nel codice Aegis |
| 📋 | Documentato / procedurale |
| ⚙️ | Richiede configurazione OS/infra |
| ❌ | Non applicabile (cloud / internet) |

---

## 1. Controllo degli accessi

| Requisito | Standard | Stato | Note |
|---|---|---|---|
| Autenticazione multi-fattore | ISO 27001 A.9.4 | 📋 | MFA locale (TOTP) pianificato per Fase 7 |
| RBAC con principio least-privilege | NIST AC-2, AC-3 | ✅ | `RBACEnforcer`, 22 permessi granulari |
| Revoca accessi utente | NIST AC-2 | ✅ | `deactivate_user()` + revoca sessioni |
| Timeout sessione | ISO 27001 A.9.4.2 | ✅ | JWT scadenza configurabile (default 1h) |
| Password policy | NIST IA-5 | ✅ | Argon2id, policy configurabile |
| Audit accessi privilegiati | NIST AU-2 | ✅ | Ogni operazione su audit log immutabile |

---

## 2. Crittografia

| Requisito | Standard | Stato | Note |
|---|---|---|---|
| Cifratura dati a riposo | GDPR Art. 32(a), NIST SC-28 | ✅ + ⚙️ | AES-256-GCM in-app + LUKS2 OS |
| Cifratura backup | ISO 27001 A.12.3 | ✅ | File `.aeb` AES-256-GCM |
| Gestione chiavi | NIST SC-12 | ✅ | `LocalKeyStore` con kid, rotazione |
| KDF per passphrase | NIST SP 800-132 | ✅ | PBKDF2-HMAC-SHA256 × 600.000 iter |
| Nessun algoritmo deprecated | NIST SP 800-131A | ✅ | Solo AES-256-GCM, SHA-256, Argon2id |
| TLS tra client e server | NIST SC-8 | 📋 | Nginx/TLS proxy documentato; Uvicorn HTTP su loopback accettabile |

---

## 3. Integrità

| Requisito | Standard | Stato | Note |
|---|---|---|---|
| Integrità software (modelli AI) | NIST SI-7 | ✅ | SHA-256 register + verify pre-load |
| Integrità log di audit | NIST AU-9 | ✅ | HMAC-SHA256 chain per ogni riga |
| Integrità backup | NIST CP-9 | ✅ | AES-GCM tag autentica il contenuto |
| Protezione da modifica non autorizzata | ISO 27001 A.14.2 | ✅ | Permessi filesystem + RBAC |

---

## 4. Disponibilità e continuità

| Requisito | Standard | Stato | Note |
|---|---|---|---|
| Backup regolari | ISO 27001 A.12.3, NIST CP-9 | ✅ | `POST /security/backup/create` |
| Test di restore | ISO 27001 A.12.3 | 📋 | Procedura mensile documentata in `hardening.md` |
| Recovery point objective (RPO) | NIST CP-2 | 📋 | Definire in base alla frequenza di backup |
| Systemd restart on failure | NIST CP-10 | ⚙️ | `Restart=on-failure` in `aegis.service` |

---

## 5. Audit e tracciabilità

| Requisito | Standard | Stato | Note |
|---|---|---|---|
| Log immutabile di tutte le azioni | GDPR Art. 30, NIST AU-2 | ✅ | `AuditWriter` append-only + HMAC chain |
| Conservazione log | NIST AU-11 | 📋 | Default: 90 giorni; configurabile |
| Log errori di autenticazione | NIST AU-2(d) | ✅ | Login fallito registrato in audit log |
| Protezione log da cancellazione | NIST AU-9 | ✅ | HMAC chain + permesso `AUDIT_READ` only |

---

## 6. Privacy (GDPR)

| Articolo | Requisito | Stato | Note |
|---|---|---|---|
| Art. 25 | Privacy by design | ✅ | Nessun dato esce dalla macchina; no telemetria |
| Art. 32(a) | Pseudonimizzazione e cifratura | ✅ | AES-256-GCM, Argon2id per password |
| Art. 32(b) | Riservatezza, integrità, disponibilità | ✅ | RBAC + cifratura + backup |
| Art. 32(c) | Ripristino tempestivo | 📋 | Procedura restore documentata |
| Art. 32(d) | Verifica periodica misure | 📋 | Checklist da eseguire ogni 6 mesi |
| Art. 17 | Diritto alla cancellazione | ✅ | `deactivate_user()` + purge dati su richiesta |

---

## 7. Non applicabile (air-gapped)

| Requisito | Motivazione esclusione |
|---|---|
| IdP cloud / SSO | Nessuna connessione internet |
| Certificate Authority pubblica (TLS) | CA interna o self-signed su LAN |
| SIEM cloud | Log solo locali |
| CDN / WAF cloud | Non applicabile |
| Telemetria / APM cloud | Vincolo architetturale |

---

## 8. Verifica periodica (ogni 6 mesi)

```
□ Aggiornare dipendenze Python (wheelhouse pinned)
□ Ruotare JWT_SECRET_KEY
□ Ruotare passphrase keystore (POST /security/keys/rotate)
□ Verificare chain audit log (POST /security/audit/verify)
□ Verificare integrità modelli (POST /security/models/{id}/verify)
□ Test di restore backup
□ Revisione utenti attivi e ruoli (GET /security/users)
□ Revisione permessi filesystem
□ pip-audit --local su wheelhouse aggiornato
□ Aggiornare questo documento se cambiano procedure
```
