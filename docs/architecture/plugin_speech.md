# Phase 7 — Plugin Engine & Speech Engine

## Plugin Engine

### Plugin contract (SDK)

Every plugin is a directory containing:

```
my-plugin/
├── aegis_plugin.json   # manifest (required)
├── main.py             # entry_point (default)
└── data/               # plugin's read-only data dir
```

**`aegis_plugin.json` schema:**
```json
{
  "plugin_id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Does X locally.",
  "author": "Your Name",
  "permissions": ["fs_read"],
  "entry_point": "main.py",
  "signature": "<hmac-sha256-hex>"
}
```

**Allowed permissions:**

| Permission | Grants |
|---|---|
| `fs_read` | Read files inside plugin's own `data/` dir only |
| `db_read` | Read-only access to local SQLite |
| `memory_read` | Read conversation memory |
| `inference` | Call local inference engine |

**Denied forever (not grantable under any circumstances):**
`network`, `fs_write_global`, `exec`, `shell`

### Sandbox guarantees

| Mechanism | What it blocks |
|---|---|
| Restricted `__import__` | All network modules: `socket`, `ssl`, `http`, `urllib`, `requests`, `httpx`, `aiohttp`, `websocket`, `urllib3`, and 15+ others |
| Removed builtins | `eval`, `exec`, `compile`, `breakpoint`, `open` (replaced with sandboxed version) |
| `fs_read` safe open | Plugins can only `open()` files inside their own `data/` dir, read mode only |
| `RLIMIT_CPU` (Unix) | 10-second CPU time cap per plugin load |
| `RLIMIT_AS` (Unix) | 256 MB virtual memory cap |

### Plugin signing

Generate a signing key and store it in `.env`:
```bash
py -c "import secrets; print(secrets.token_hex(32))"
# PLUGIN_SIGNING_KEY=<output> in .env
```

Sign a plugin before distribution:
```python
from backend.infrastructure.plugin.manifest import load_manifest, sign_manifest
manifest = load_manifest(Path("my-plugin"))
sig = sign_manifest(manifest, b"<your-key>")
print(sig)  # place in aegis_plugin.json > "signature"
```

### Lifecycle

```
Install  →  plugin dir copied to plugins/, manifest validated + checksum stored
Enable   →  sandbox loaded, entry_point executed, status = ACTIVE
Call     →  sandbox.call(method, payload) with resource caps
Disable  →  sandbox released, status = INACTIVE
Uninstall→  dir deleted, registry entry removed
```

### REST API (`/api/v1/plugins`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/plugins` | List all installed plugins |
| `GET` | `/api/v1/plugins/{id}` | Get plugin manifest |
| `POST` | `/api/v1/plugins/{id}/enable` | Load + activate plugin |
| `POST` | `/api/v1/plugins/{id}/disable` | Unload plugin |
| `POST` | `/api/v1/plugins/{id}/call` | Call a plugin method |
| `GET` | `/api/v1/plugins/{id}/integrity` | Verify entry_point checksum |
| `DELETE` | `/api/v1/plugins/{id}` | Uninstall plugin |

---

## Speech Engine

### STT: faster-whisper

Completely offline Whisper inference via CTranslate2.

**Install (once, air-gap machine):**
```bash
pip install faster-whisper
# Download model (internet machine then copy):
huggingface-cli download Systran/faster-whisper-small \
    --local-dir models/whisper/faster-whisper-small
```

**Model directory:** `models/whisper/<model-id>/`

Available variants: `faster-whisper-tiny`, `faster-whisper-small`, `faster-whisper-medium`, `faster-whisper-large-v3`

### TTS: Coqui + pyttsx3 fallback

| Engine | Install | Quality | Offline |
|---|---|---|---|
| Coqui TTS | `pip install TTS` | High | ✅ (model files copied) |
| pyttsx3 | `pip install pyttsx3` | System voices | ✅ (always available) |

Model directory for Coqui: `models/tts/coqui-tts/`

### REST API (`/api/v1/speech`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/speech/transcribe` | Upload WAV/OGG → text |
| `POST` | `/api/v1/speech/synthesize` | Text → WAV audio bytes |
| `GET` | `/api/v1/speech/models/stt` | List available STT models |
| `GET` | `/api/v1/speech/voices/tts` | List available TTS voices |

---

## Air-gap compliance

- All plugin code executes in-process with no subprocess/shell.
- `WhisperModel(..., local_files_only=True)` — CTranslate2 never contacts HuggingFace Hub.
- Coqui TTS loads from a local directory path — no model download.
- pyttsx3 uses OS speech synthesizer — fully offline.
