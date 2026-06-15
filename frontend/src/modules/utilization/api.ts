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
  overdue_milestones: unknown[] | null
  projected_revenue_inr: number | null
  actual_revenue_inr: number | null
  total_cost_inr: number | null
}

export async function fetchCompanyDashboard(): Promise<CompanyDashboard> {
  const { data } = await api.get<{ data: CompanyDashboard }>('/dashboard/company')
  return data.data
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
}

export async function fetchAvailability(window = 30): Promise<AvailabilityData> {
  const { data } = await api.get<{ data: AvailabilityData }>(`/dashboard/availability?window=${window}`)
  return data.data
}
