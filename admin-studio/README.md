# Admin Studio

React + Vite admin dashboard for the **Aegis** AI platform (air-gapped, offline-first).

## Stack

| Tool | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | 5 | Dev server + bundler |
| TypeScript | 5 | Type safety |
| React Router | 6 | Client-side routing |
| Zustand | 4 | Global state |
| CSS Modules | — | Scoped component styles |

## Architecture

```
src/
├── App.tsx                   # Root router with RequireAuth guard
├── main.tsx                  # Vite entry point
├── components/
│   ├── layout/               # AppShell, Sidebar, Topbar
│   └── ui/                   # Design system primitives
├── hooks/
│   ├── useAuth.ts            # Auth state convenience hook
│   ├── usePermissions.ts     # can() / canAll() / canAny()
│   └── usePagination.ts      # Client-side pagination
├── lib/
│   ├── api-client.ts         # Fetch wrapper — all calls → local FastAPI /api/v1
│   └── query-keys.ts         # Centralized cache key constants
├── pages/                    # One file per route
│   ├── LoginPage             # Public
│   ├── DashboardPage         # /dashboard
│   ├── AssistantsPage        # /assistants
│   ├── AssistantDetailPage   # /assistants/:id
│   ├── KnowledgePage         # /knowledge
│   ├── ModelsPage            # /models
│   ├── TrainingPage          # /training
│   ├── UsersPage             # /users
│   ├── RolesPage             # /roles
│   ├── SessionsPage          # /sessions
│   ├── AuditPage             # /audit
│   ├── PluginsPage           # /plugins
│   ├── WorkflowsPage         # /workflows
│   ├── FeatureTogglesPage    # /features
│   ├── LanguagesPage         # /languages
│   ├── TemplatesPage         # /templates
│   ├── BackupPage            # /backup
│   ├── MonitoringPage        # /monitoring
│   └── SettingsPage          # /settings
└── store/
    ├── auth.store.ts         # JWT token + user profile
    ├── ui.store.ts           # Theme + sidebar state
    └── toast.store.ts        # Global toast notifications
```

## Dev Commands

```bash
# Install dependencies (requires Node 20+)
cd admin-studio
npm install

# Start dev server (proxies /api/v1 → http://localhost:8000)
npm run dev

# Type-check
npm run typecheck

# Lint
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Air-Gapped Install

```bash
# On a connected machine: pack all npm deps
npm pack --dry-run   # verify
npm ci               # install to node_modules
tar czf admin-studio-node_modules.tar.gz node_modules/

# On the air-gapped machine:
tar xzf admin-studio-node_modules.tar.gz
npm run build        # uses local node_modules, no network
```

## Permission Model

Every page uses `useAuthStore((s) => s.hasPermission)` or the `usePermissions()` hook to gate writes.
Superadmins bypass all checks. Permissions follow the pattern `resource:action`, e.g.:

- `users:read` / `users:write`
- `roles:read` / `roles:write`
- `backup:write` / `backup:restore`
- `admin:settings:write`
- `features:write`

## Security Notes

- JWT token stored **in-memory only** (`window.__aegis_token`), never in localStorage/sessionStorage.
- All API calls target `/api/v1` on the same origin — no cross-origin requests.
- No telemetry, no analytics, no external fonts loaded at runtime (CDN-free in production — bundle fonts locally if needed).
