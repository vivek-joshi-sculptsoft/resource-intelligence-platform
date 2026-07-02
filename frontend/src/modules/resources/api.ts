import api from '../../shared/lib/axios'
import type { PaginatedResponse } from '../../shared/types/api'

export interface ResourceListItem {
  id: string
  employee_id: string
  name: string
  designation: string
  technical_expertise: string | null
  total_allocation_pct: number
  is_active: boolean
  tags: string[]
  loaded_cost_monthly: number | null
}

export interface ResourceDetail {
  id: string
  employee_id: string
  name: string
  designation: string
  technical_expertise: string | null
  date_of_joining: string | null
  reporting_manager: { id: string; name: string } | null
  loaded_cost_monthly: number | null
  is_active: boolean
  tags: string[]
  total_allocation_pct: number
  created_at: string
}

export interface ResourceCreatePayload {
  employee_id: string
  name: string
  designation: string
  technical_expertise?: string
  date_of_joining?: string
  reporting_manager_id?: string | null
  tags?: string[]
  loaded_cost_monthly?: number | null
}

export interface ResourceUpdatePayload {
  employee_id?: string
  name?: string
  designation?: string
  technical_expertise?: string
  date_of_joining?: string
  reporting_manager_id?: string | null
  loaded_cost_monthly?: number | null
}

export interface ResourceFilters {
  page?: number
  limit?: number
  status?: string
  designation?: string
  expertise?: string
  tag?: string
  availability?: string
  search?: string
}

export async function fetchResources(filters: ResourceFilters = {}): Promise<PaginatedResponse<ResourceListItem>> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== '') params.set(k, String(v))
  })
  const { data } = await api.get(`/resources?${params.toString()}`)
  return data
}

export async function fetchResource(id: string): Promise<{ data: ResourceDetail }> {
  const { data } = await api.get(`/resources/${id}`)
  return data
}

export async function createResource(payload: ResourceCreatePayload): Promise<{ data: ResourceDetail }> {
  const { data } = await api.post('/resources', payload)
  return data
}

export async function updateResource(id: string, payload: ResourceUpdatePayload): Promise<{ data: ResourceDetail }> {
  const { data } = await api.put(`/resources/${id}`, payload)
  return data
}

export async function deleteResource(id: string): Promise<void> {
  await api.delete(`/resources/${id}`)
}

export async function addResourceTag(id: string, tag: string): Promise<{ data: { tags: string[] } }> {
  const { data } = await api.post(`/resources/${id}/tags`, { tag })
  return data
}

export async function removeResourceTag(id: string, tag: string): Promise<{ data: { tags: string[] } }> {
  const { data } = await api.delete(`/resources/${id}/tags/${encodeURIComponent(tag)}`)
  return data
}

export async function fetchResourcesDropdown(): Promise<{ id: string; name: string; employee_id: string }[]> {
  const { data } = await api.get('/resources?limit=100&status=ACTIVE')
  return data.data.map((r: ResourceListItem) => ({ id: r.id, name: r.name, employee_id: r.employee_id }))
}

// See BUSINESS-RULES.md §7.6 — bench cost fields are Decimal, serialized as JSON strings
export interface ResourceBenchCost {
  days_on_bench: number | null
  daily_bench_cost_inr: number | null
  total_bench_cost_inr: number | null
  bench_start_date: string | null
}

export async function fetchResourceBenchCost(id: string): Promise<ResourceBenchCost | null> {
  const { data } = await api.get(`/resources/${id}/bench-cost`)
  const raw = data.data
  if (raw === null) return null
  return {
    ...raw,
    daily_bench_cost_inr: raw.daily_bench_cost_inr === null ? null : Number(raw.daily_bench_cost_inr),
    total_bench_cost_inr: raw.total_bench_cost_inr === null ? null : Number(raw.total_bench_cost_inr),
  }
}
