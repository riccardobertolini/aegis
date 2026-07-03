/**
 * Thin API client re-exports for Admin Studio.
 *
 * NOTE:
 * - `api`, `ApiError`, `setGlobalToken` restano per compatibilità.
 * - Named clients `systemApi`, `usageApi`, `assistantsApi`,
 *   `languagesApi`, `templatesApi`, `workflowsApi` sono wrapper
 *   sottili sopra `api` per evitare errori di import in Vite.
 */

import { api, ApiError, setGlobalToken } from './api-client'

export { api, ApiError, setGlobalToken }

// Types di base — adatta ai tuoi DTO reali se già definiti altrove.
type Id = string

export interface SystemStatus {
  status: string
  uptimeSeconds: number
}

export interface UsageOverview {
  requests: number
  tokens: number
}

export interface AssistantCreate {
  name: string
  description?: string
  modelId?: string
}

export interface LanguageUpsert {
  code: string
  name: string
  enabled: boolean
}

export interface TemplateCreate {
  name: string
  description?: string
  content: string
}

export interface WorkflowCreate {
  name: string
  description?: string
  definition: unknown
}

// ----- systemApi -----

export const systemApi = {
  async getStatus(): Promise<SystemStatus> {
    const res = await api.get('/api/system/status')
    return res.data as SystemStatus
  },
}

// ----- usageApi -----

export const usageApi = {
  async getOverview(): Promise<UsageOverview> {
    const res = await api.get('/api/system/usage')
    return res.data as UsageOverview
  },
}

// ----- assistantsApi -----

export const assistantsApi = {
  async list() {
    const res = await api.get('/api/assistants')
    return res.data
  },

  async getById(id: Id) {
    const res = await api.get(`/api/assistants/${id}`)
    return res.data
  },

  async create(payload: AssistantCreate) {
    const res = await api.post('/api/assistants', payload)
    return res.data
  },

  async update(id: Id, payload: Partial<AssistantCreate>) {
    const res = await api.put(`/api/assistants/${id}`, payload)
    return res.data
  },

  async remove(id: Id) {
    const res = await api.delete(`/api/assistants/${id}`)
    return res.data
  },
}

// ----- languagesApi -----

export const languagesApi = {
  async list() {
    const res = await api.get('/api/languages')
    return res.data
  },

  async upsert(payload: LanguageUpsert) {
    const res = await api.post('/api/languages', payload)
    return res.data
  },

  async remove(code: string) {
    const res = await api.delete(`/api/languages/${code}`)
    return res.data
  },
}

// ----- templatesApi -----

export const templatesApi = {
  async list() {
    const res = await api.get('/api/templates')
    return res.data
  },

  async create(payload: TemplateCreate) {
    const res = await api.post('/api/templates', payload)
    return res.data
  },

  async update(id: Id, payload: Partial<TemplateCreate>) {
    const res = await api.put(`/api/templates/${id}`, payload)
    return res.data
  },

  async remove(id: Id) {
    const res = await api.delete(`/api/templates/${id}`)
    return res.data
  },
}

// ----- workflowsApi -----

export const workflowsApi = {
  async list() {
    const res = await api.get('/api/workflows')
    return res.data
  },

  async create(payload: WorkflowCreate) {
    const res = await api.post('/api/workflows', payload)
    return res.data
  },

  async update(id: Id, payload: Partial<WorkflowCreate>) {
    const res = await api.put(`/api/workflows/${id}`, payload)
    return res.data
  },

  async remove(id: Id) {
    const res = await api.delete(`/api/workflows/${id}`)
    return res.data
  },
}