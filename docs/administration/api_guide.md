# Administration Engine — API Guide

## Scope

The Administration Engine exposes a complete local REST API (FastAPI on
`localhost:8000`) that both **Admin Studio** and **Client** use to orchestrate
the platform. All endpoints are air-gapped and restricted to loopback by
`LocalOnlyMiddleware`.

## Base URL

```
http://127.0.0.1:8000
```

OpenAPI docs: `http://127.0.0.1:8000/docs` (Swagger UI)
ReDoc: `http://127.0.0.1:8000/redoc`

## Authentication

All write endpoints (`POST`, `PATCH`, `PUT`, `DELETE`) require a Bearer token
issued by the Security Engine (Phase 6). Pass it in the `Authorization` header:

```
Authorization: Bearer <jwt-token>
```

## Endpoint Map

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/health` | System health |
| GET/POST | `/admin/assistants` | List / create assistants |
| GET/PATCH/DELETE | `/admin/assistants/{id}` | Get / update / delete |
| POST | `/admin/assistants/{id}/duplicate` | Clone with new name |
| GET/POST | `/admin/templates` | List / create templates |
| DELETE | `/admin/templates/{id}` | Delete template |
| GET/POST | `/admin/workflows` | List / create workflows |
| PATCH/DELETE | `/admin/workflows/{id}` | Update / delete workflow |
| GET/POST | `/admin/rules` | List / create rules |
| DELETE | `/admin/rules/{id}` | Delete rule |
| GET/POST | `/admin/categories` | List / create categories |
| DELETE | `/admin/categories/{id}` | Delete category |
| GET | `/admin/features` | List feature toggles |
| PUT | `/admin/features` | Set feature toggle |
| GET | `/admin/features/{key}` | Check single toggle |
| GET | `/admin/languages` | List language configs |
| PUT | `/admin/languages` | Upsert language config |
| GET | `/admin/users` | List users |
| POST | `/admin/users` | Create user |
| DELETE | `/admin/users/{id}` | Delete user |
| GET | `/admin/models` | List loaded models |
| GET | `/admin/datasets` | List datasets |
| GET | `/admin/experiments` | List experiments |
| POST | `/admin/backup` | Create local backup |
| POST | `/admin/restore` | Restore from backup |
| GET | `/admin/config/export` | Export full config (JSON) |
| POST | `/admin/config/import` | Import config from JSON |
| POST | `/admin/usage/query` | Query usage events |
| GET | `/admin/usage/stats` | Aggregated usage stats |

## Localhost-only enforcement

`LocalOnlyMiddleware` checks the remote IP of every request to `/admin/*` and
`/auth/*`. If the IP is not `127.x.x.x` or `::1`, the request is rejected
with HTTP 403. This guarantees that even if the process is exposed on a
network interface by misconfiguration, the administration surface remains
inaccessible remotely.

## Feature Toggles

Feature toggles are managed at runtime without redeployment:

```bash
curl -X PUT http://127.0.0.1:8000/admin/features \
  -H 'Content-Type: application/json' \
  -d '{"key": "rag_enabled", "enabled": true, "description": "Enable RAG pipeline"}'
```

## Config Export / Import

Export the full platform configuration to a JSON file for archival or
migration to another air-gapped machine:

```bash
curl http://127.0.0.1:8000/admin/config/export > aegis-config-$(date +%Y%m%d).json
```

Import on the target machine:

```bash
curl -X POST http://127.0.0.1:8000/admin/config/import \
  -H 'Content-Type: application/json' \
  -d @aegis-config-20260102.json
```

## Usage Monitoring

All inference, training, and document operations can record a `UsageEvent`
via `AdminService.record_usage(...)`. Query them:

```bash
curl -X POST http://127.0.0.1:8000/admin/usage/query \
  -H 'Content-Type: application/json' \
  -d '{"event_type": "inference", "limit": 50}'
```

## OpenAPI schema (local generation)

```bash
python - <<'EOF'
import json
from backend.main import create_app
app = create_app()
with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
print("Written to openapi.json")
EOF
```
