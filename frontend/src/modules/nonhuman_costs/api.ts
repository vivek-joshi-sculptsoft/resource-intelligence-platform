// See FSD §2.10 — NonHumanCost API client
import axios from 'axios'

const BASE = '/api/v1'

export interface CostEntry {
  id: string
  project_id: string
  description: string
  category: string
  amount: number
  currency: string
  exchange_rate: number
  amount_inr: number
  cost_date: string
  is_recurring: boolean
  recurring_end_date: string | null
  created_by: { id: string; name: string } | null
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface CostSummary {
  total_inr: number
  by_category: Record<string, number>
  one_time_inr: number
  recurring_monthly_inr: number
}

export interface ListCostsParams {
  category?: string
  is_recurring?: boolean
  date_from?: string
  date_to?: string
  page?: number
  limit?: number
}

export interface CostPayload {
  description: string
  category: string
  amount: number
  currency: string
  exchange_rate?: number
  cost_date: string
  is_recurring: boolean
  recurring_end_date?: string | null
}

export async function fetchCosts(projectId: string, params: ListCostsParams = {}) {
  const { data } = await axios.get(`${BASE}/projects/${projectId}/costs`, { params })
  return data
}

export async function fetchCostSummary(projectId: string): Promise<CostSummary> {
  const { data } = await axios.get(`${BASE}/projects/${projectId}/costs/summary`)
  return data
}

export async function createCost(projectId: string, payload: CostPayload) {
  const { data } = await axios.post(`${BASE}/projects/${projectId}/costs`, payload)
  return data
}

export async function updateCost(projectId: string, costId: string, payload: Partial<CostPayload>) {
  const { data } = await axios.put(`${BASE}/projects/${projectId}/costs/${costId}`, payload)
  return data
}

export async function deleteCost(projectId: string, costId: string) {
  const { data } = await axios.delete(`${BASE}/projects/${projectId}/costs/${costId}`)
  return data
}
