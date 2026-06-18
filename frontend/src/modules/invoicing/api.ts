// See FSD §2.8 — Milestone API client
import api from '../../shared/lib/axios'

export interface Milestone {
  id: string
  project_id: string
  name: string
  amount: number | null
  planned_delivery_date: string | null
  actual_delivery_date: string | null
  status: MilestoneStatus
  sort_order: number | null
  is_delayed: boolean
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export type MilestoneStatus = 'PLANNED' | 'DELIVERED' | 'APPROVED' | 'INVOICED' | 'PAID'

export interface MilestoneCreatePayload {
  name: string
  amount: number
  planned_delivery_date?: string | null
  sort_order?: number | null
}

export interface MilestoneUpdatePayload {
  name?: string
  amount?: number
  planned_delivery_date?: string | null
  sort_order?: number | null
}

export async function fetchMilestones(projectId: string): Promise<{ data: Milestone[] }> {
  const { data } = await api.get(`/projects/${projectId}/milestones`)
  return data
}

export async function createMilestone(projectId: string, payload: MilestoneCreatePayload): Promise<{ data: Milestone }> {
  const { data } = await api.post(`/projects/${projectId}/milestones`, payload)
  return data
}

export async function updateMilestone(projectId: string, milestoneId: string, payload: MilestoneUpdatePayload): Promise<{ data: Milestone }> {
  const { data } = await api.put(`/projects/${projectId}/milestones/${milestoneId}`, payload)
  return data
}

export async function transitionMilestoneStatus(projectId: string, milestoneId: string, status: MilestoneStatus): Promise<{ data: Milestone }> {
  const { data } = await api.put(`/projects/${projectId}/milestones/${milestoneId}/status`, { status })
  return data
}

// See FSD §2.9 — Invoice API client

export type InvoiceStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'PAID'

export interface Invoice {
  id: string
  project_id: string
  milestone_id: string | null
  invoice_date: string | null
  amount: number | null
  currency: string
  exchange_rate: number | null
  amount_inr: number | null
  billing_period_start: string | null
  billing_period_end: string | null
  status: InvoiceStatus
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string | null
  milestone: Milestone | null
}

export interface InvoiceCreatePayload {
  invoice_date: string
  amount: number
  currency: string
  exchange_rate?: number | null
  milestone_id?: string | null
  billing_period_start?: string | null
  billing_period_end?: string | null
  notes?: string | null
}

export type InvoiceUpdatePayload = Partial<InvoiceCreatePayload>

export async function fetchInvoices(
  projectId: string,
  status?: string,
): Promise<{ data: Invoice[]; total: number; page: number; limit: number }> {
  const { data } = await api.get(`/projects/${projectId}/invoices`, { params: status ? { status } : undefined })
  return data
}

export async function createInvoice(projectId: string, payload: InvoiceCreatePayload): Promise<{ data: Invoice }> {
  const { data } = await api.post(`/projects/${projectId}/invoices`, payload)
  return data
}

export async function updateInvoice(projectId: string, invoiceId: string, payload: InvoiceUpdatePayload): Promise<{ data: Invoice }> {
  const { data } = await api.put(`/projects/${projectId}/invoices/${invoiceId}`, payload)
  return data
}

export async function transitionInvoiceStatus(projectId: string, invoiceId: string, status: InvoiceStatus): Promise<{ data: Invoice }> {
  const { data } = await api.put(`/projects/${projectId}/invoices/${invoiceId}/status`, { status })
  return data
}

// See FSD §6.3 — Receivables API client

export interface Receivable extends Invoice {
  project_name: string | null
  client_id: string | null
  client_name: string | null
}

export async function fetchReceivables(status?: string): Promise<{ data: Receivable[] }> {
  const { data } = await api.get('/invoices/receivables', { params: status ? { status } : undefined })
  return data
}
