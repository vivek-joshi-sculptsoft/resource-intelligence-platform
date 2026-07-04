import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { InfoTooltip, type InfoTooltipContent } from '../../../shared/components/InfoTooltip'
import { fetchCompanyFinanceDashboard, type CompanyFinanceFilters } from '../api'
import { fetchProjects, type ProjectListItem } from '../../projects/api'
import { fetchClients, type ClientListItem } from '../../clients/api'

function formatInr(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—'
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatPct(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—'
  return val.toFixed(1) + '%'
}

// See modules/07-utilization-dashboards/SCREENS.md — Info Tooltips for finance KPI cards
const KPI_TOOLTIPS: Record<string, InfoTooltipContent> = {
  actualRevenue: {
    formula: 'SUM(invoice.amount_inr) WHERE status IN (APPROVED, PAID) AND invoice_date ∈ period',
    meaning: 'Invoiced revenue actually recognized in the selected period',
    purpose: 'Source of truth for financial reporting; the number Finance reconciles against',
  },
  projectedRevenue: {
    formula: 'SUM(billability_pct/100 × working_days_in_period × 8 × billing_rate) for non-shadow assignments overlapping the period',
    meaning: 'Expected billable revenue from active assignments over the selected period',
    purpose: 'Forward-looking revenue signal; compare against actual to spot invoicing lag or shortfall',
  },
  totalCost: {
    formula: 'Resource Cost (period) + Non-Human Cost (period)',
    meaning: 'Total cost to deliver — resource loaded cost plus non-human costs (licenses, infra, etc.) in the period',
    purpose: 'Denominator for margin; the full cost base leadership is accountable for',
  },
  companyMargin: {
    formula: '(Revenue − Total Cost) / Revenue × 100, shown for both projected and actual',
    meaning: 'Company-wide profitability after all resource and non-human costs, for the selected period/filters',
    purpose: 'Bottom-line profitability indicator — the headline number for this screen',
  },
}

type RangeOption = 'THIS_MONTH' | 'LAST_3_MONTHS' | 'CUSTOM'

export function CompanyFinanceDashboard() {
  const [range, setRange] = useState<RangeOption>('THIS_MONTH')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [projectId, setProjectId] = useState('')
  const [clientId, setClientId] = useState('')

  const filters: CompanyFinanceFilters = { range }
  if (range === 'CUSTOM' && startDate && endDate) {
    filters.start_date = startDate
    filters.end_date = endDate
  }
  if (projectId) filters.project_id = projectId
  if (clientId) filters.client_id = clientId

  const enabled = range !== 'CUSTOM' || (!!startDate && !!endDate && endDate >= startDate)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['company-finance-dashboard', filters],
    queryFn: () => fetchCompanyFinanceDashboard(filters),
    enabled,
  })

  const { data: projectsData } = useQuery({
    queryKey: ['projects-list-for-filter'],
    queryFn: () => fetchProjects({ limit: 200 }),
  })

  const { data: clientsData } = useQuery({
    queryKey: ['clients-list-for-filter'],
    queryFn: () => fetchClients({ limit: 200 }),
  })

  const projects: ProjectListItem[] = projectsData?.data ?? []
  const clients: ClientListItem[] = clientsData?.data ?? []

  // See SCREENS.md — selecting a project auto-scopes the client dropdown to that project's client
  const selectedProject = projects.find((p: ProjectListItem) => p.id === projectId)
  const filteredClients = projectId && selectedProject?.client_id
    ? clients.filter((c: ClientListItem) => c.id === selectedProject.client_id)
    : clients

  return (
    <div>
      {/* Page Header */}
      <div className="mb-5">
        <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>
          Company Finance Dashboard
        </h1>
        <p className="mt-0.5 text-[13px]" style={{ color: '#6b7280' }}>
          Revenue, cost, and margin — filter by period, project, or client
        </p>
      </div>

      {/* Filter Bar */}
      <div
        className="mb-6 flex flex-wrap items-center gap-4 rounded-xl border border-[#E8EAF6] bg-white p-3.5 px-5"
        style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        {/* Time filter buttons */}
        <div
          className="flex gap-1 rounded-lg border border-[#E8EAF6] p-[3px]"
          style={{ background: '#F5F6FC' }}
        >
          {(['THIS_MONTH', 'LAST_3_MONTHS', 'CUSTOM'] as RangeOption[]).map((opt) => (
            <button
              key={opt}
              onClick={() => setRange(opt)}
              className="rounded-md border-none px-3.5 py-1.5 text-[12px] font-medium transition-all"
              style={{
                background: range === opt ? '#2B3990' : 'transparent',
                color: range === opt ? '#fff' : '#6b7280',
                fontWeight: range === opt ? 600 : 500,
                cursor: 'pointer',
              }}
            >
              {opt === 'THIS_MONTH' ? 'This Month' : opt === 'LAST_3_MONTHS' ? 'Last 3 Months' : 'Custom'}
            </button>
          ))}
        </div>

        {/* Custom date range pickers */}
        {range === 'CUSTOM' && (
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded-lg border border-[#D6DAF0] px-2.5 py-1.5 text-[12px]"
              style={{ background: '#F0F1FA', color: '#1e1b4b' }}
            />
            <span className="text-[12px]" style={{ color: '#7C85C0' }}>to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              min={startDate}
              className="rounded-lg border border-[#D6DAF0] px-2.5 py-1.5 text-[12px]"
              style={{ background: '#F0F1FA', color: '#1e1b4b' }}
            />
          </div>
        )}

        {/* Divider */}
        <div className="h-8 w-px self-stretch" style={{ background: '#E8EAF6' }} />

        {/* Project filter */}
        <div className="flex flex-col gap-[3px]">
          <label className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: '#7C85C0' }}>
            Project
          </label>
          <select
            value={projectId}
            onChange={(e) => {
              setProjectId(e.target.value)
              if (e.target.value) {
                const proj = projects.find((p: ProjectListItem) => p.id === e.target.value)
                if (proj?.client_id) setClientId(proj.client_id)
              }
            }}
            className="min-w-[180px] rounded-lg border border-[#D6DAF0] bg-white px-2.5 py-1.5 text-[13px]"
            style={{ color: '#1e1b4b' }}
          >
            <option value="">All Projects</option>
            {projects.map((p: ProjectListItem) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Client filter */}
        <div className="flex flex-col gap-[3px]">
          <label className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: '#7C85C0' }}>
            Client
          </label>
          <select
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="min-w-[180px] rounded-lg border border-[#D6DAF0] bg-white px-2.5 py-1.5 text-[13px]"
            style={{ color: '#1e1b4b' }}
          >
            <option value="">All Clients</option>
            {filteredClients.map((c: ClientListItem) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading / Error */}
      {isLoading && (
        <div className="py-12 text-center text-[14px]" style={{ color: '#7C85C0' }}>
          Loading financial data...
        </div>
      )}
      {isError && (
        <div className="py-12 text-center text-[14px]" style={{ color: '#ef4444' }}>
          Failed to load finance data. Please try again.
        </div>
      )}

      {data && (
        <>
          {/* KPI Grid — 4 cards */}
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Total Revenue (Actual) */}
            <KpiCard
              label="Total Revenue (Actual)"
              value={formatInr(data.actual_revenue_inr)}
              sub="From approved & paid invoices"
              detail={`${data.period_start} – ${data.period_end}`}
              accentGradient="linear-gradient(90deg, #059669, #34d399)"
              textColor="#059669"
              tooltip={KPI_TOOLTIPS.actualRevenue}
            />

            {/* Total Projected Revenue */}
            <KpiCard
              label="Total Projected Revenue"
              value={formatInr(data.projected_revenue_inr)}
              sub={
                data.actual_revenue_inr > 0
                  ? (() => {
                      const diff = ((data.projected_revenue_inr - data.actual_revenue_inr) / data.actual_revenue_inr) * 100
                      const isUp = diff >= 0
                      return (
                        <span style={{ color: isUp ? '#16a34a' : '#ef4444', fontWeight: 600 }}>
                          {isUp ? '▲' : '▼'} {Math.abs(diff).toFixed(1)}% vs actual
                        </span>
                      )
                    })()
                  : 'From active assignments in period'
              }
              detail="From active assignments in period"
              accentGradient="linear-gradient(90deg, #2B3990, #4A5BB5)"
              textColor="#2B3990"
              tooltip={KPI_TOOLTIPS.projectedRevenue}
            />

            {/* Total Cost */}
            <KpiCard
              label="Total Cost"
              value={formatInr(data.total_cost_inr)}
              sub={`Resource: ${formatInr(data.resource_cost_inr)} · Non-Human: ${formatInr(data.non_human_cost_inr)}`}
              accentGradient="linear-gradient(90deg, #ea580c, #f59e0b)"
              textColor="#ea580c"
              tooltip={KPI_TOOLTIPS.totalCost}
            />

            {/* Company Margin */}
            <KpiCard
              label="Company Margin"
              value={formatPct(data.projected_margin_pct)}
              sub={`Actual: ${formatPct(data.actual_margin_pct)}`}
              accentGradient="linear-gradient(90deg, #FF4B2B, #FF7043)"
              textColor="#FF4B2B"
              tooltip={KPI_TOOLTIPS.companyMargin}
            />
          </div>

          {/* Margin Detail Card */}
          <div
            className="mb-6 rounded-xl border border-[#E8EAF6] bg-white"
            style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
          >
            <div className="flex items-center justify-between border-b border-[#E8EAF6] px-5 py-4">
              <h3 className="text-[15px] font-bold" style={{ color: '#1e1b4b' }}>Margin Detail</h3>
            </div>
            <div className="px-5 py-5">
              <div className="flex items-center justify-between border-b border-[#E8EAF6] py-2.5 text-[13px]">
                <span className="font-semibold" style={{ color: '#1e1b4b' }}>Projected Margin</span>
                <span className="font-bold" style={{ color: '#16a34a' }}>
                  {formatInr(data.projected_margin_inr)} ({formatPct(data.projected_margin_pct)})
                </span>
              </div>
              <div className="flex items-center justify-between py-2.5 text-[13px]">
                <span className="font-semibold" style={{ color: '#1e1b4b' }}>Actual Margin</span>
                <span className="font-bold" style={{ color: '#f59e0b' }}>
                  {formatInr(data.actual_margin_inr)} ({formatPct(data.actual_margin_pct)})
                </span>
              </div>

              {data.projects_with_incomplete_financial_data > 0 && (
                <div className="mt-3 text-[12px]" style={{ color: '#ea580c' }}>
                  ⚠ {data.projects_with_incomplete_financial_data} project{data.projects_with_incomplete_financial_data > 1 ? 's' : ''} missing cost/rate data — totals above are incomplete until every active assignment has a loaded cost / billing rate set.
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Empty state when enabled but no data */}
      {data && data.actual_revenue_inr === 0 && data.projected_revenue_inr === 0 && data.total_cost_inr === 0 && (
        <div className="py-12 text-center">
          <div className="mb-4 text-[48px]">📊</div>
          <h3 className="text-[16px] font-semibold" style={{ color: '#1e1b4b' }}>
            No financial data for this period
          </h3>
          <p className="mt-1 text-[13px]" style={{ color: '#6b7280' }}>
            Try widening the date range or clearing the project/client filter.
          </p>
        </div>
      )}
    </div>
  )
}

function KpiCard({
  label,
  value,
  sub,
  detail,
  accentGradient,
  textColor,
  tooltip,
}: {
  label: string
  value: string
  sub?: React.ReactNode
  detail?: string
  accentGradient: string
  textColor: string
  tooltip: InfoTooltipContent
}) {
  return (
    <div
      className="relative overflow-hidden rounded-xl border border-[#E8EAF6] bg-white p-5"
      style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
    >
      <div
        className="absolute top-0 left-0 right-0 h-[3px]"
        style={{ background: accentGradient }}
      />
      <div className="mb-2 flex items-center gap-1.5 text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#7C85C0' }}>
        {label}
        <InfoTooltip content={tooltip} />
      </div>
      <div className="text-[30px] font-extrabold leading-none" style={{ color: textColor }}>
        {value}
      </div>
      {sub && (
        <div className="mt-1.5 text-[12px]" style={{ color: '#6b7280' }}>
          {sub}
        </div>
      )}
      {detail && (
        <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>
          {detail}
        </div>
      )}
    </div>
  )
}
