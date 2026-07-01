// See FSD §7.2-§7.5 — Project financials API client
import axios from 'axios'

const BASE = '/api/v1'

export interface ResourceCostBreakdownItem {
  resource_name: string
  resource_designation: string
  allocation_pct: number
  loaded_cost_monthly: number | null
  cost_contribution_inr: number | null
}

export interface ProjectFinancials {
  resource_cost_inr: number | null
  non_human_cost_inr: number | null
  total_cost_inr: number | null
  projected_revenue_inr: number | null
  actual_revenue_inr: number | null
  projected_margin_inr: number | null
  projected_margin_pct: number | null
  actual_margin_inr: number | null
  actual_margin_pct: number | null
  resource_cost_breakdown: ResourceCostBreakdownItem[]
  missing_costs: string[]
  missing_rates: string[]
  exchange_rate_used: number | null
}

// Decimal fields are serialized as JSON strings by Pydantic — coerce to numbers here
// so the rest of the app can treat this response as plain numeric data.
function n(val: string | number | null): number | null {
  return val === null ? null : Number(val)
}

export async function fetchProjectFinancials(projectId: string): Promise<ProjectFinancials> {
  const { data } = await axios.get(`${BASE}/projects/${projectId}/financials`)
  const raw = data.data
  return {
    ...raw,
    resource_cost_inr: n(raw.resource_cost_inr),
    non_human_cost_inr: n(raw.non_human_cost_inr),
    total_cost_inr: n(raw.total_cost_inr),
    projected_revenue_inr: n(raw.projected_revenue_inr),
    actual_revenue_inr: n(raw.actual_revenue_inr),
    projected_margin_inr: n(raw.projected_margin_inr),
    projected_margin_pct: n(raw.projected_margin_pct),
    actual_margin_inr: n(raw.actual_margin_inr),
    actual_margin_pct: n(raw.actual_margin_pct),
    exchange_rate_used: n(raw.exchange_rate_used),
    resource_cost_breakdown: raw.resource_cost_breakdown.map((r: ResourceCostBreakdownItem) => ({
      ...r,
      loaded_cost_monthly: n(r.loaded_cost_monthly),
      cost_contribution_inr: n(r.cost_contribution_inr),
    })),
  }
}
