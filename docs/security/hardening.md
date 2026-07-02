# Aegis — Hardening Guide

This guide documents OS-level and application-level hardening steps required for a
production air-gapped deployment. All steps must be applied in addition to the
application-layer controls implemented in Fase 6.

---

## OS-Level Hardening

### 1. Disk Encryption
```bash
# LUKS2 full-disk encryption (Linux)
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 --key-size 512 \
  --hash sha256 /dev/sdX
```
- Mandatory prerequisite for protecting `keystore.bin` and `.env` at rest.
- Without disk encryption, physical access = full compromise.

### 2. Filesystem Permissions
```bash
# Aegis data directory: owner-only read/write
chmod 700 data/
chmod 600 data/security/keystore.bin
chmod 600 .env
chmod 640 data/aegis.db
chmod 750 models/
```

### 3. Process Isolation
```bash
# Run as dedicated non-root user
useradd --system --no-create-home --shell /usr/sbin/nologin aegis
chown -R aegis:aegis /opt/aegis
```

### 4. Systemd Hardening (optional but recommended)
```ini
# /etc/systemd/system/aegis.service
[Service]
User=aegis
Group=aegis
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aegis/data /opt/aegis/logs
PrivateTmp=true
CapabilityBoundingSet=
AmbientCapabilities=
RestrictSUIDSGID=true
LockPersonality=true
RestrictRealtime=true
```

### 5. Network Hardening
```bash
# Bind Uvicorn to localhost only (reverse proxy handles TLS if needed)
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# iptables: block all outbound except localhost (air-gap enforcement)
iptables -P OUTPUT DROP
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

---

## Application Hardening

### JWT Secret
```bash
# Generate a cryptographically strong secret
python -c "import secrets; print(secrets.token_hex(32))"
# Set in .env: JWT_SECRET_KEY=<output>
```

### Password Policy
Enforce at user creation time (Admin Studio UI should validate):
- Minimum 12 characters
- At least one uppercase, lowercase, digit, special character
- No username in password
- No common passwords (check against rockyou-100k locally)

### First-Run Bootstrap
```bash
# After deployment, immediately change the default superadmin password
curl -X POST http://localhost:8000/security/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "ChangeMe123!"}'
# Then update via the Admin Studio UI
```

### Key Rotation Schedule
- Rotate encryption keys every 90 days (`POST /security/keys/rotate`)
- Rotate JWT secret every 180 days (restart required, invalidates all sessions)
- After rotation, re-encrypt any column-level encrypted data using the new key

### Session Hardening
- Session duration: 60 minutes (configurable via `JWT_EXPIRY_MINUTES`)
- Server-side session revocation available at any time
- List and revoke sessions: `GET /security/sessions`

---

## Secure Boot (Optional)

For environments requiring hardware-rooted trust:

1. **Enable UEFI Secure Boot** on the host hardware.
2. **TPM 2.0 seal** the LUKS key to PCR values (requires `systemd-cryptenroll`):
   ```bash
   systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=0+7 /dev/sdX
   ```
3. **IMA/EVM** (Integrity Measurement Architecture): measure all Python files at boot.
   Configure in `/etc/ima/ima-policy`.
4. **Application attestation**: on startup, Aegis can verify its own model hashes
   before accepting inference requests. Use `POST /security/models/verify`.

---

## Backup Hardening

```bash
# Create encrypted backup
curl -X POST http://localhost:8000/security/backup/create \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"source_path": "data", "dest_path": "data/backups"}'

# Verify backup integrity before offsite storage
file data/backups/aegis_backup_*.aeb  # should show: data

# Store backups on encrypted external media only
# Never transmit backups over unencrypted channels
```

---

## Audit Log Monitoring

```bash
# Verify audit chain integrity (should be run daily)
# Via the AuditReader.verify_chain() method, callable from CLI:
python -c "
import asyncio
from backend.infrastructure.security.audit import AuditReader
# ... (wire up session and key)
"

# Watch for suspicious patterns:
# - Multiple 'denied' outcomes for same actor_id
# - 'auth.login' failures > 3 in 5 minutes
# - Any 'admin:full' action outside business hours
```
