import { apiClient } from './client'

export interface ConversationSummary {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ConversationDetail {
  id: string
  messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: string }>
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const { data } = await apiClient.get<ConversationSummary[]>('/memory/conversations')
  return data
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/memory/conversations/${id}`)
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const { data } = await apiClient.get<ConversationDetail>(`/memory/conversations/${id}`)
  return data
}
