/** Centralised TanStack Query key factory. */
export const qk = {
  // Auth
  me:          () => ['me'] as const,
  sessions:    () => ['sessions'] as const,

  // Assistants
  assistants:  (params?: object) => ['assistants', params] as const,
  assistant:   (id: string)      => ['assistant', id] as const,

  // Knowledge
  kbList:      (assistantId?: string) => ['kb', assistantId] as const,
  kbDoc:       (id: string)           => ['kb-doc', id] as const,
  categories:  (assistantId?: string) => ['categories', assistantId] as const,

  // Plugins
  plugins:     () => ['plugins'] as const,
  plugin:      (id: string) => ['plugin', id] as const,

  // Users & RBAC
  users:       (params?: object) => ['users', params] as const,
  user:        (id: string)      => ['user', id] as const,
  roles:       () => ['roles'] as const,
  permissions: () => ['permissions'] as const,

  // Models
  models:      () => ['models'] as const,
  model:       (id: string) => ['model', id] as const,

  // Training & datasets
  trainJobs:   () => ['train-jobs'] as const,
  datasets:    () => ['datasets'] as const,
  dataset:     (id: string) => ['dataset', id] as const,

  // Workflows
  workflows:   () => ['workflows'] as const,
  workflow:    (id: string) => ['workflow', id] as const,

  // Feature toggles
  features:    () => ['features'] as const,

  // Languages
  languages:   () => ['languages'] as const,

  // Backup
  backups:     () => ['backups'] as const,

  // Audit & monitoring
  auditLog:    (params?: object) => ['audit', params] as const,
  metrics:     (range?: string)  => ['metrics', range] as const,

  // Memory
  memory:      (assistantId?: string) => ['memory', assistantId] as const,

  // Templates
  templates:   () => ['templates'] as const,

  // Versions
  versions:    (assistantId?: string) => ['versions', assistantId] as const,
}
