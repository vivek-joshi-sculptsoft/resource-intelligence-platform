import api from '../../shared/lib/axios'

export interface BenchResource {
  id: string
  name: string
  designation: string
  days_on_bench: number
}

export interface UpcomingRelease {
  resource_name: string
  project_name: string
  end_date: string
  days_remaining: number
}

export interface OverdueMilestone {
  id: string
  project_id: string
  project_name: string
  name: string
  planned_delivery_date: string
  days_overdue: number
}

export interface CompanyDashboard {
  billable_utilization_pct: number
  total_active_resources: number
  bench_count: number
  bench_resources: BenchResource[]
  shadow_count: number
  shadow_total_allocation_pct: number
  active_project_count: number
  active_projects_by_type: Record<string, number>
  upcoming_releases_30d: UpcomingRelease[]
  overdue_milestones_count: number | null
  overdue_milestones: OverdueMilestone[] | null
  resource_cost_inr: number | null
  non_human_cost_inr: number | null
  projected_revenue_inr: number | null
  actual_revenue_inr: number | null
  total_cost_inr: number | null
  projected_margin_inr: number | null
  projected_margin_pct: number | null
  actual_margin_inr: number | null
  actual_margin_pct: number | null
  overall_margin_pct: number | null
  total_bench_cost_monthly: number | null
}

// Decimal fields are serialized as JSON strings by Pydantic — coerce to numbers so
// the rest of the app can do arithmetic on this response without surprises.
function n(val: string | number | null | undefined): number | null {
  return val === null || val === undefined ? null : Number(val)
}

export async function fetchCompanyDashboard(): Promise<CompanyDashboard> {
  const { data } = await api.get<{ data: CompanyDashboard }>('/dashboard/company')
  const raw = data.data
  return {
    ...raw,
    billable_utilization_pct: Number(raw.billable_utilization_pct),
    resource_cost_inr: n(raw.resource_cost_inr),
    non_human_cost_inr: n(raw.non_human_cost_inr),
    projected_revenue_inr: n(raw.projected_revenue_inr),
    actual_revenue_inr: n(raw.actual_revenue_inr),
    total_cost_inr: n(raw.total_cost_inr),
    projected_margin_inr: n(raw.projected_margin_inr),
    projected_margin_pct: n(raw.projected_margin_pct),
    actual_margin_inr: n(raw.actual_margin_inr),
    actual_margin_pct: n(raw.actual_margin_pct),
    overall_margin_pct: n(raw.overall_margin_pct),
    total_bench_cost_monthly: n(raw.total_bench_cost_monthly),
  }
}

export interface DMDashboard {
  portfolio_utilization_pct: number
  active_project_count: number
  resource_count: number
  bench_count: number
  upcoming_releases_30d: UpcomingRelease[]
  delivery_delays: unknown[] | null
  projected_revenue_inr: number | null
  total_cost_inr: number | null
}

export async function fetchDMDashboard(): Promise<DMDashboard> {
  const { data } = await api.get<{ data: DMDashboard }>('/dashboard/dm')
  return data.data
}

export interface AvailabilityBenchResource {
  id: string
  name: string
  designation: string
  technical_expertise: string | null
  days_on_bench: number
  tags: string[]
  bench_cost_daily: number | null
  bench_cost_total: number | null
}

export interface AvailabilityPartialResource {
  id: string
  name: string
  designation: string
  total_allocation_pct: number
  spare_capacity_pct: number
  projects: string[]
}

export interface AvailabilityReleasingSoon {
  resource_id: string
  name: string
  designation: string
  project_name: string
  allocation_pct: number
  end_date: string
  days_remaining: number
}

export interface AvailabilityFullyAllocated {
  id: string
  name: string
  designation: string
  total_allocation_pct: number
  projects: string[]
}

export interface AvailabilityData {
  bench: AvailabilityBenchResource[]
  partial: AvailabilityPartialResource[]
  releasing_soon: AvailabilityReleasingSoon[]
  fully_allocated: AvailabilityFullyAllocated[]
  can_see_bench_cost: boolean
  total_bench_cost_monthly: number | null
}

export async function fetchAvailability(window = 30): Promise<AvailabilityData> {
  const { data } = await api.get<{ data: AvailabilityData }>(`/dashboard/availability?window=${window}`)
  return data.data
}
