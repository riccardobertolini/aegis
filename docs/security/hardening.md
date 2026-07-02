# Aegis — Hardening Guide

> Deployment air-gapped. Nessun servizio cloud richiesto.

---

## 1. OS Hardening (Linux)

### 1.1 Full-Disk Encryption (LUKS2) — OBBLIGATORIO

```bash
# Durante installazione OS: cifrare la partizione dati
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
  --key-size 512 --hash sha512 /dev/sdX

# Aprire e montare
cryptsetup luksOpen /dev/sdX aegis_crypt
mkfs.ext4 /dev/mapper/aegis_crypt
mount /dev/mapper/aegis_crypt /opt/aegis
```

In alternativa, usare l'installer grafico di Ubuntu/Debian con opzione "Encrypt disk".

### 1.2 Utente dedicato

```bash
useradd -m -s /bin/bash -d /opt/aegis aegis
chmod 750 /opt/aegis
# Eseguire Uvicorn come utente aegis, non come root
sudo -u aegis uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 1.3 Firewall host (iptables / ufw)

```bash
# Consentire solo loopback e porta 8000 da LAN se necessario
ufw default deny incoming
ufw allow from 127.0.0.1 to any port 8000
# Se multi-utente LAN:
# ufw allow from 192.168.1.0/24 to any port 8000
ufw enable
```

### 1.4 Filesystem permissions

```bash
# .env mai leggibile da altri utenti
chmod 600 /opt/aegis/.env
chown aegis:aegis /opt/aegis/.env

# Cartella modelli
chmod 700 /opt/aegis/models
chown aegis:aegis /opt/aegis/models

# Keystore
chmod 600 /opt/aegis/data/keystore.json
```

### 1.5 systemd service (hardened)

```ini
# /etc/systemd/system/aegis.service
[Unit]
Description=Aegis AI Backend
After=network.target

[Service]
Type=simple
User=aegis
Group=aegis
WorkingDirectory=/opt/aegis
ExecStart=/opt/aegis/.venv/bin/uvicorn backend.main:app \
  --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aegis/data /opt/aegis/logs /opt/aegis/backups
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service

[Install]
WantedBy=multi-user.target
```

---

## 2. Application Hardening

### 2.1 JWT

- Scadenza massima consigliata: **60 minuti** (default in `config.py`)
- `jwt_secret_key` generato con `secrets.token_hex(32)` e conservato fuori dal repo
- Rotazione chiave JWT: aggiorna `JWT_SECRET_KEY` in `.env` e riavvia
- Ogni token include `jti` (UUID) verificato contro DB → revoca immediata possibile

### 2.2 Password policy

Minimo consigliato (configurabile in `SecuritySettings`):
- Lunghezza ≥ 12 caratteri
- Almeno 1 maiuscola, 1 minuscola, 1 cifra, 1 carattere speciale
- Nessuna delle ultime 5 password riusata
- Scadenza opzionale ogni 90 giorni

### 2.3 Rate limiting

Aggiungere `slowapi` o middleware custom su `/security/login`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

### 2.4 Keystore passphrase

- Minimo **20 caratteri**, mix di classi
- Non nel file `.env` in testo chiaro in produzione: usare `systemd` `LoadCredential` o un secrets manager locale (Hashicorp Vault air-gapped)
- Ruotare il keystore ogni 90 giorni con `POST /security/keys/rotate`

### 2.5 Backup

- Backup `.aeb` su supporto separato (NAS cifrato, USB LUKS)
- Test di restore mensile documentato
- Passphrase backup separata da passphrase keystore

---

## 3. Secure Boot (opzionale)

Secure Boot garantisce che solo software firmato venga eseguito al boot.

### Abilitare Secure Boot

1. **BIOS/UEFI**: abilitare Secure Boot, impostare modalità "Custom"
2. **Generare chiavi**: `openssl req -new -x509 -newkey rsa:2048 -keyout db.key -out db.crt -days 3650 -subj "/CN=Aegis Secure Boot/"`
3. **Firmare bootloader**: `sbsign --key db.key --cert db.crt --output grubx64.efi.signed grubx64.efi`
4. **Importare chiave in UEFI db**
5. **Verificare**: `mokutil --sb-state` → `SecureBoot enabled`

> ⚠️ Secure Boot non sostituisce LUKS2. Usare entrambi.

---

## 4. Dependency Security

```bash
# Audit dipendenze (offline-compatible)
pip install pip-audit
pip-audit --local  # analizza solo pacchetti installati, no download

# Generare wheelhouse pinned con hash
pip download -r requirements/base.txt -d wheelhouse/
pip hash wheelhouse/*.whl > requirements/hashes.txt

# Installazione air-gapped verificata
pip install --no-index --find-links wheelhouse/ \
  --require-hashes -r requirements/hashes.txt
```

---

## 5. Checklist pre-produzione

- [ ] LUKS2 attivo e testato
- [ ] Utente dedicato `aegis` non-root
- [ ] `ufw` configurato
- [ ] `.env` chmod 600
- [ ] `JWT_SECRET_KEY` ≥ 32 byte random, fuori repo
- [ ] Passphrase keystore ≥ 20 char, fuori `.env`
- [ ] Audit chain verificata: `POST /security/audit/verify`
- [ ] Hash modelli registrati: `POST /security/models/register`
- [ ] Backup test-restore completato
- [ ] `systemd` service con hardening attivo
- [ ] Log rotation configurato
