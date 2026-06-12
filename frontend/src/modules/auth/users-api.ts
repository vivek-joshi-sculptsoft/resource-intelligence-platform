import api from '../../shared/lib/axios'
import type { Role, User } from './api'

export interface UserListItem {
  id: string
  name: string
  email: string
  role: Role
  resource_id: string | null
  is_active: boolean
  created_at: string
}

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  total_pages: number
}

export interface UsersListResponse {
  data: UserListItem[]
  meta: PaginationMeta
}

export interface CreateUserPayload {
  email: string
  name: string
  password: string
  role_id: string
  resource_id?: string | null
}

export interface UpdateUserPayload {
  name?: string
  role_id?: string
  resource_id?: string | null
  is_active?: boolean
  password?: string
}

export async function fetchUsers(params: {
  page?: number
  limit?: number
  status?: string
  search?: string
}): Promise<UsersListResponse> {
  const { data } = await api.get<UsersListResponse>('/users', { params })
  return data
}

export async function fetchUser(id: string): Promise<UserListItem> {
  const { data } = await api.get<{ data: UserListItem }>(`/users/${id}`)
  return data.data
}

export async function createUser(payload: CreateUserPayload): Promise<UserListItem> {
  const { data } = await api.post<{ data: UserListItem }>('/users', payload)
  return data.data
}

export async function updateUser(id: string, payload: UpdateUserPayload): Promise<UserListItem> {
  const { data } = await api.put<{ data: UserListItem }>(`/users/${id}`, payload)
  return data.data
}

export async function fetchRoles(): Promise<{ data: Role[] }> {
  const resp = await api.get<{ data: any[] }>('/roles')
  return resp.data
}
