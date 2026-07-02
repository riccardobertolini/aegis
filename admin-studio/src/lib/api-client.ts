/**
 * API Client — all requests routed to local FastAPI backend.
 * No external network calls. Interceptors attach Bearer token from authStore.
 */

const BASE_URL = '/api/v1'

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    message?: string,
  ) {
    super(message ?? detail)
    this.name = 'ApiError'
  }
}

function getToken(): string | null {
  // Read from in-memory auth store (no localStorage in air-gapped context)
  // Dynamically imported to avoid circular deps
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any
    return w.__aegis_token ?? null
  } catch {
    return null
  }
}

export function setGlobalToken(token: string | null): void {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(window as any).__aegis_token = token
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { signal?: AbortSignal; formData?: FormData },
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {}

  if (token) headers['Authorization'] = `Bearer ${token}`
  if (body && !options?.formData) headers['Content-Type'] = 'application/json'

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: options?.formData ?? (body ? JSON.stringify(body) : undefined),
    signal: options?.signal,
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const json = await response.json()
      detail = json?.detail ?? detail
    } catch {/* ignore */}
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string, signal?: AbortSignal) =>
    request<T>('GET', path, undefined, { signal }),

  post:   <T>(path: string, body?: unknown) =>
    request<T>('POST', path, body),

  put:    <T>(path: string, body?: unknown) =>
    request<T>('PUT', path, body),

  patch:  <T>(path: string, body?: unknown) =>
    request<T>('PATCH', path, body),

  delete: <T>(path: string) =>
    request<T>('DELETE', path),

  upload: <T>(path: string, formData: FormData) =>
    request<T>('POST', path, undefined, { formData }),
}
