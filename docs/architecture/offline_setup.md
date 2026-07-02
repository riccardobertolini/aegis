# Offline / Air-Gapped Setup

## Building the Wheelhouse

Run this on a machine with internet access:

```bash
# Python deps
pip download -r requirements/base.txt  -d wheelhouse/
pip download -r requirements/dev.txt   -d wheelhouse/
pip download -r requirements/ml.txt    -d wheelhouse/ml/

# Node deps (admin-studio)
cd admin-studio && npm ci
npx npm-offline-packager   # or: npm pack each dep

# Node deps (client)
cd ../client && npm ci
```

Ship the `wheelhouse/` directory and `node_modules/` tarballs to the air-gapped machine.

## Installing on Air-Gapped Machine

```bash
# Python
pip install --no-index --find-links=wheelhouse/ -r requirements/base.txt

# Node (admin-studio)
cd admin-studio
npm install --offline

# Node (client)
cd ../client
npm install --offline
```

## Model Distribution

- Models are never downloaded automatically.
- Models must be copied manually to `models/` (USB, internal network share).
- The Inference Engine scans `AEGIS_MODELS_DIR` at startup.
- Supported format: Mamba checkpoint `.pt` + config `.json`.

## Certificate / TLS (optional)

For internal HTTPS, generate a self-signed cert and place it in `certs/`:

```bash
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 3650 -nodes
```
