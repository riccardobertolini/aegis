import { apiClient } from './client'

export interface DocumentMeta {
  id: string
  title: string
  file_type: string
  size_bytes: number
  status: 'indexing' | 'indexed' | 'error'
  created_at: string
}

export async function listDocuments(): Promise<DocumentMeta[]> {
  const { data } = await apiClient.get<DocumentMeta[]>('/documents/')
  return data
}

export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<DocumentMeta> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<DocumentMeta>('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return data
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}`)
}
