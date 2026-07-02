/**
 * Aegis API client — all calls to localhost:8000.
 * No external network. Token from auth store injected per-request.
 */

const BASE = ''  // Vite proxy → http://127.0.0.1:8000

let _getToken: () => string | null = () => null

export function setTokenGetter(fn: () => string | null) {
  _getToken = fn
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const token = _getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try { const j = await res.json(); msg = j.detail ?? msg } catch {}
    throw new Error(msg)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const get  = <T>(p: string)            => request<T>('GET',    p)
const post = <T>(p: string, b: unknown)=> request<T>('POST',   p, b)
const put  = <T>(p: string, b: unknown)=> request<T>('PUT',    p, b)
const patch= <T>(p: string, b: unknown)=> request<T>('PATCH',  p, b)
const del  = <T>(p: string)            => request<T>('DELETE', p)

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    post<{ access_token: string; token_type: string }>('/auth/login', { username, password }),
  logout: () => post('/auth/logout', {}),
}

// System
export const systemApi = {
  health: () => get<{ status: string; components: Record<string,string>; warnings: string[] }>('/admin/health'),
}

// Assistants
export const assistantsApi = {
  list:      (active?: boolean) => get<Assistant[]>(`/admin/assistants${active ? '?active_only=true' : ''}`),
  get:       (id: number) => get<Assistant>(`/admin/assistants/${id}`),
  create:    (b: AssistantCreate) => post<Assistant>('/admin/assistants', b),
  update:    (id: number, b: Partial<AssistantCreate>) => patch<Assistant>(`/admin/assistants/${id}`, b),
  delete:    (id: number) => del<void>(`/admin/assistants/${id}`),
  duplicate: (id: number, new_name: string) => post<Assistant>(`/admin/assistants/${id}/duplicate`, { new_name }),
}

// Templates
export const templatesApi = {
  list:   () => get<Template[]>('/admin/templates'),
  create: (b: TemplateCreate) => post<Template>('/admin/templates', b),
  delete: (id: number) => del<void>(`/admin/templates/${id}`),
}

// Workflows
export const workflowsApi = {
  list:   (active?: boolean) => get<Workflow[]>(`/admin/workflows${active ? '?active_only=true' : ''}`),
  create: (b: WorkflowCreate) => post<Workflow>('/admin/workflows', b),
  update: (id: number, b: Partial<WorkflowCreate>) => patch<Workflow>(`/admin/workflows/${id}`, b),
  delete: (id: number) => del<void>(`/admin/workflows/${id}`),
}

// Rules
export const rulesApi = {
  list:   () => get<Rule[]>('/admin/rules'),
  create: (b: RuleCreate) => post<Rule>('/admin/rules', b),
  delete: (id: number) => del<void>(`/admin/rules/${id}`),
}

// Categories
export const categoriesApi = {
  list:   () => get<Category[]>('/admin/categories'),
  create: (b: CategoryCreate) => post<Category>('/admin/categories', b),
  delete: (id: number) => del<void>(`/admin/categories/${id}`),
}

// Feature toggles
export const featuresApi = {
  list:   () => get<FeatureToggle[]>('/admin/features'),
  set:    (key: string, enabled: boolean, description?: string) =>
    put<FeatureToggle>('/admin/features', { key, enabled, description: description ?? '' }),
  check:  (key: string) => get<{ key: string; enabled: boolean }>(`/admin/features/${key}`),
}

// Languages
export const languagesApi = {
  list:   () => get<LanguageConfig[]>('/admin/languages'),
  upsert: (b: LanguageUpsert) => put<LanguageConfig>('/admin/languages', b),
}

// Users
export const usersApi = {
  list:   () => get<User[]>('/admin/users'),
  create: (b: UserCreate) => post<User>('/admin/users', b),
  delete: (id: string) => del<void>(`/admin/users/${id}`),
}

// Models / Datasets / Experiments
export const modelsApi = {
  list:        () => get<{ models: string[] }>('/admin/models'),
  datasets:    () => get<{ datasets: string[] }>('/admin/datasets'),
  experiments: () => get<{ experiments: unknown[] }>('/admin/experiments'),
}

// Backup
export const backupApi = {
  create:  (b: BackupRequest) => post<{ backup_path: string }>('/admin/backup', b),
  restore: (backup_path: string) => post<{ status: string }>('/admin/restore', { backup_path }),
}

// Config
export const configApi = {
  export: () => get<Record<string, unknown>>('/admin/config/export'),
  import: (data: Record<string, unknown>) => post<{ imported: Record<string,number> }>('/admin/config/import', { data }),
}

// Usage
export const usageApi = {
  query: (b: UsageQuery) => post<UsageEvent[]>('/admin/usage/query', b),
  stats: (event_type?: string) =>
    get<UsageStats>(`/admin/usage/stats${event_type ? `?event_type=${event_type}` : ''}`),
}

// ---------- Domain types ----------
export interface Assistant {
  id: number; name: string; description: string; model_id: string;
  system_prompt: string; template_id: number | null; is_active: boolean;
  created_at: string; updated_at: string; meta: string;
}
export interface AssistantCreate {
  name: string; description?: string; model_id?: string;
  system_prompt?: string; template_id?: number | null; meta?: string;
}
export interface Template {
  id: number; name: string; description: string; system_prompt: string;
  default_model_id: string; is_builtin: boolean; created_at: string; meta: string;
}
export interface TemplateCreate {
  name: string; description?: string; system_prompt?: string;
  default_model_id?: string; meta?: string;
}
export interface Workflow {
  id: number; name: string; description: string; steps: string;
  is_active: boolean; created_at: string; updated_at: string;
}
export interface WorkflowCreate {
  name: string; description?: string; steps?: string;
}
export interface Rule {
  id: number; name: string; description: string; condition: string;
  action: string; priority: number; is_active: boolean; created_at: string;
}
export interface RuleCreate {
  name: string; description?: string; condition?: string;
  action?: string; priority?: number;
}
export interface Category {
  id: number; name: string; slug: string;
  parent_id: number | null; description: string; created_at: string;
}
export interface CategoryCreate {
  name: string; slug: string; parent_id?: number | null; description?: string;
}
export interface FeatureToggle {
  id: number; key: string; enabled: boolean; description: string; updated_at: string;
}
export interface LanguageConfig {
  id: number; code: string; label: string;
  is_enabled: boolean; is_default: boolean; updated_at: string;
}
export interface LanguageUpsert {
  code: string; label: string; is_enabled?: boolean; is_default?: boolean;
}
export interface User {
  id: string; username: string; roles: string[]; is_active: boolean; created_at: string;
}
export interface UserCreate {
  username: string; password: string; roles: string[];
}
export interface BackupRequest {
  destination_path: string; include_models?: boolean; compress?: boolean;
}
export interface UsageQuery {
  event_type?: string; user_id?: string; since?: string; limit?: number;
}
export interface UsageEvent {
  id: number; event_type: string; user_id: string | null;
  model_id: string | null; tokens_used: number;
  duration_ms: number; status: string; occurred_at: string; meta: string;
}
export interface UsageStats {
  total_events: number; total_tokens: number; avg_duration_ms: number; event_type: string;
}
