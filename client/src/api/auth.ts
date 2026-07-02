import { apiClient } from './client'

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const { data } = await apiClient.post<LoginResponse>('/security/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/security/logout')
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiClient.post('/security/users/me/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
