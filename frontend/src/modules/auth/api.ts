import api from '../../shared/lib/axios'

export interface Role {
  id: string
  code: string
  name: string
  permission_level: number
}

export interface User {
  id: string
  name: string
  email: string
  role: Role
  resource_id: string | null
}

export interface LoginResponse {
  user: User
}

export async function loginApi(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password })
  return data
}

export async function logoutApi(): Promise<void> {
  await api.post('/auth/logout')
}

export async function getMeApi(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function refreshTokenApi(): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/refresh')
  return data
}
