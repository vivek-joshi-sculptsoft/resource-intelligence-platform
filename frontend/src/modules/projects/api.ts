import api from '../../shared/lib/axios'
import type { PaginatedResponse } from '../../shared/types/api'

export interface ProjectListItem {
  id: string
  name: string
  client_name: string
  type: string
  status: string
  billing_currency: string
  dm_name: string
  pm_name: string
  start_date: string | null
  contract_end_date: string | null
}

export interface RelatedEntity {
  id: string
  name: string
}

export interface ProjectDetail {
  id: string
  name: string
  client: RelatedEntity
  type: string
  status: string
  billing_currency: string
  contract_value: number | null
  start_date: string | null
  contract_end_date: string | null
  dm: RelatedEntity
  pm: RelatedEntity
  worklog_enabled: boolean
  notes: string | null
  created_at: string
}

export interface ProjectCreatePayload {
  name: string
  client_id: string
  type: string
  billing_currency?: string
  start_date?: string | null
  contract_end_date?: string | null
  dm_id: string
  pm_id: string
  worklog_enabled?: boolean
  notes?: string | null
}

export interface ProjectFilters {
  page?: number
  limit?: number
  status?: string
  type?: string
  client_id?: string
  dm_id?: string
  search?: string
}

export async function fetchProjects(filters: ProjectFilters = {}): Promise<PaginatedResponse<ProjectListItem>> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== '') params.set(k, String(v))
  })
  const { data } = await api.get(`/projects?${params.toString()}`)
  return data
}

export async function fetchProject(id: string): Promise<{ data: ProjectDetail }> {
  const { data } = await api.get(`/projects/${id}`)
  return data
}

export async function createProject(payload: ProjectCreatePayload): Promise<{ data: ProjectDetail }> {
  const { data } = await api.post('/projects', payload)
  return data
}

export async function updateProject(id: string, payload: Partial<ProjectCreatePayload>): Promise<{ data: ProjectDetail }> {
  const { data } = await api.put(`/projects/${id}`, payload)
  return data
}

export async function transitionProjectStatus(id: string, status: string): Promise<{ data: ProjectDetail }> {
  const { data } = await api.put(`/projects/${id}/status`, { status })
  return data
}
