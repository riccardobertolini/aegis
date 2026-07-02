import { apiClient } from './client'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  use_rag?: boolean
}

export interface ChatResponse {
  conversation_id: string
  reply: string
  intent?: string
  sources?: Array<{ document_id: string; title: string; excerpt: string }>
}

export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>('/intent/chat', req)
  return data
}
