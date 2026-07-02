# Aegis — Threat Model

> Versione: 1.0  
> Data: 2026-07-02  
> Scope: backend API + storage locale, deployment air-gapped

---

## 1. Asset di alto valore

| Asset | Confidenzialità | Integrità | Disponibilità |
|---|---|---|---|
| Modelli SSM (pesi) | Alta | Critica | Alta |
| Documenti / indici vettoriali | Alta | Alta | Alta |
| Chiavi di cifratura (keystore) | Critica | Critica | Alta |
| Audit log | Media | Critica | Alta |
| Credenziali utente (hash Argon2id) | Critica | Alta | Media |
| Backup cifrati (`.aeb`) | Alta | Alta | Media |
| Configurazione / .env | Alta | Alta | Media |

---

## 2. Attori di minaccia

| Attore | Vettore | Motivazione | Livello di rischio |
|---|---|---|---|
| Utente interno malintenzionato | Accesso fisico alla macchina | Esfiltrazione dati | Alto |
| Insider con credenziali valide | API locale | Privilege escalation | Alto |
| Attaccante con accesso fisico temporaneo | USB / boot esterno | Lettura disco | Medio |
| Attaccante remoto (se rete interna compromessa) | HTTP LAN | Injection, auth bypass | Medio |
| Software supply chain | Dipendenze Python | Backdoor, data exfil | Medio |

---

## 3. Analisi STRIDE

### S — Spoofing (Impersonation)

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Furto di JWT | Token in-memory / header | Token breve scadenza (1h), revocation server-side in `security_sessions` |
| Brute-force credenziali | `/security/login` | Argon2id (slow hash) + rate-limit applicativo |
| Session fixation | Login flow | Nuovo session_id a ogni autenticazione |

### T — Tampering

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Modifica pesi modello | File su disco | SHA-256 registrato al deploy, `verify_model_integrity()` prima di ogni load |
| Modifica audit log | SQLite `audit_logs` | HMAC-SHA256 chained rows — ogni riga firma quella precedente |
| Modifica backup | File `.aeb` | AES-256-GCM authenticated encryption — ogni modifica invalida il tag |
| Modifica configurazione | `.env` / DB | File `.env` owned root:root 600; config firmata opzionalmente |

### R — Repudiation

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Negare azioni compiute | Qualsiasi operazione | Audit log immutabile con user_id, timestamp, action, resource, HMAC chain |
| Manomissione log post-hoc | `audit_logs` | Chain HMAC; `verify_audit_chain()` rilevabile anche da DB esterno |

### I — Information Disclosure

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Lettura disco (accesso fisico) | SQLite, modelli, indici | LUKS2 full-disk encryption (OS-level, documentato in `hardening.md`) |
| Leak in log applicativi | structlog | Nessuna PII, password, token nei log; livello INFO in produzione |
| Errori verbose in API | FastAPI exception handlers | Handler globale → risposta generica; dettagli solo in log interni |
| Keystore passphrase in env | `.env` | File fuori repo, chmod 600; passphrase mai loggata |

### D — Denial of Service

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Flood login | `/security/login` | Rate limiting middleware (configurabile) |
| Upload massiccio file | Document endpoints | Max size configurabile in settings |
| Riempimento disco (audit/backup) | Storage locale | Retention policy + alert su soglia spazio |

### E — Elevation of Privilege

| Minaccia | Componente | Mitigazione |
|---|---|---|
| Assegnazione ruolo non autorizzata | `/users/{id}/roles` | Richiede `Permission.USER_WRITE`, disponibile solo a ADMIN/SUPERADMIN |
| JWT con claim manipolati | Token decode | Firma HMAC-SHA256; verifica `jti` presente in DB e non revocato |
| SQL injection | SQLModel queries | ORM parametrizzato; nessuna query raw con interpolazione |

---

## 4. Rischi residui

| Rischio | Probabilità | Impatto | Accettato? | Note |
|---|---|---|---|---|
| Accesso fisico prolungato senza LUKS | Media | Critico | No | LUKS2 obbligatorio in produzione |
| Compromissione supply chain pip | Bassa | Alto | Condizionale | Wheelhouse pinned + hash check |
| Passphrase keystore debole | Media | Critico | No | Policy minima 20 char documentata |
| Brute-force offline hash DB | Bassa | Alto | Condizionale | Argon2id + LUKS rendono impraticabile |

---

## 5. Superficie di attacco

- **Ridotta**: nessun endpoint internet, nessun websocket esterno, nessun cloud SDK
- **Attiva**: HTTP locale (LAN / loopback), filesystem, processo Python
- **Consigliata**: bind Uvicorn su `127.0.0.1` in single-user; su IP LAN solo se necessario e con firewall host

---

## 6. Assunzioni di sicurezza

1. L'OS host è trusted e aggiornato.
2. Il disco è cifrato con LUKS2 prima del deploy.
3. La passphrase del keystore è gestita fuori banda (non in `.env` in chiaro in produzione).
4. I modelli SSM sono distribuiti tramite canale sicuro e il loro hash SHA-256 è registrato prima del primo uso.
5. L'accesso fisico alla macchina è controllato (data center, armadio chiuso).
