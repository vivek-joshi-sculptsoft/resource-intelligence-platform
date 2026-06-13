import api from '../../shared/lib/axios'
import type { PaginatedResponse } from '../../shared/types/api'

export interface ClientListItem {
  id: string
  name: string
  industry: string | null
  engagement_start_date: string | null
  active_project_count: number
  is_active: boolean
}

export interface ClientDetail {
  id: string
  name: string
  industry: string | null
  contact_name: string | null
  contact_email: string | null
  contact_phone: string | null
  engagement_start_date: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  projects: { id: string; name: string; type: string; status: string; dm_id: string | null; pm_id: string | null }[]
  dashboard: {
    active_resource_count: number
    active_project_count: number
    total_monthly_billing_inr: number | null
    total_cost_inr: number | null
    aggregate_margin_inr: number | null
    project_count_by_type: Record<string, number>
  }
}

export interface ClientCreatePayload {
  name: string
  industry?: string
  contact_name?: string
  contact_email?: string
  contact_phone?: string
  engagement_start_date?: string
  notes?: string
}

export interface ClientFilters {
  page?: number
  limit?: number
  status?: string
  search?: string
}

export async function fetchClients(filters: ClientFilters = {}): Promise<PaginatedResponse<ClientListItem>> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== '') params.set(k, String(v))
  })
  const { data } = await api.get(`/clients?${params.toString()}`)
  return data
}

export async function fetchClient(id: string): Promise<{ data: ClientDetail }> {
  const { data } = await api.get(`/clients/${id}`)
  return data
}

export async function createClient(payload: ClientCreatePayload): Promise<{ data: ClientDetail }> {
  const { data } = await api.post('/clients', payload)
  return data
}

export async function updateClient(id: string, payload: Partial<ClientCreatePayload>): Promise<{ data: ClientDetail }> {
  const { data } = await api.put(`/clients/${id}`, payload)
  return data
}

export async function deleteClient(id: string): Promise<void> {
  await api.delete(`/clients/${id}`)
}
