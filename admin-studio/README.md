# Aegis Admin Studio

Full administration UI built with React 18 + Vite.

## Structure

```
admin-studio/
  src/
    components/   # Reusable UI components
    pages/        # Route-level pages
      ModelManager/
      UserManager/
      PluginManager/
      TrainingDashboard/
      LogViewer/
      ConfigEditor/
      TimeSeriesViewer/
    hooks/        # Custom React hooks
    services/     # API client calls (fetch to local backend)
    store/        # State management
    types/        # TypeScript types
  public/
  index.html
  vite.config.ts
  package.json
```

## Setup (offline)

```bash
npm install --offline   # requires pre-downloaded node_modules tarball
npm run dev
npm run build
```
