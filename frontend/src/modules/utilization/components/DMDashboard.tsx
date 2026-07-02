import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { InfoTooltip, type InfoTooltipContent } from '../../../shared/components/InfoTooltip'
import { fetchDMDashboard, type OverdueMilestone, type UpcomingRelease } from '../api'

function formatInr(val: number | null): string {
  if (val === null) return '—'
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

// See modules/07-utilization-dashboards/SCREENS.md — Info Tooltips
const KPI_TOOLTIPS: Record<string, InfoTooltipContent> = {
  portfolioUtilization: {
    formula: 'SUM(billable_pct) for non-shadow ACTIVE assignments / (portfolio_resource_count × 100) × 100',
    meaning: 'Share of your portfolio capacity currently billed to clients',
    purpose: 'Core efficiency metric for your delivery portfolio',
  },
  portfolioRevenue: {
    formula: 'SUM(per-assignment projected revenue) for non-shadow ACTIVE assignments across portfolio',
    meaning: 'Projected billable revenue for the current month across your projects',
    purpose: 'Top-line revenue indicator for your portfolio',
  },
  portfolioCost: {
    formula: 'Resource Cost (loaded_cost × allocation %) + Non-Human Costs (INR)',
    meaning: 'Total monthly cost across your portfolio projects',
    purpose: 'Tracks cost exposure for delivery planning',
  },
  deliveryDelays: {
    formula: 'COUNT(milestones WHERE planned_delivery_date < today AND status = PLANNED)',
    meaning: 'Number of milestones past their planned delivery date',
    purpose: 'Early warning for delivery risk — delays may affect invoicing and client satisfaction',
  },
  activeProjects: {
    formula: 'COUNT(projects WHERE dm_id = you AND status = ACTIVE)',
    meaning: 'Number of active projects in your portfolio',
    purpose: 'Current delivery load indicator',
  },
  benchCount: {
    formula: 'COUNT(resources on your projects with 0 ACTIVE assignments globally)',
    meaning: 'Portfolio resources currently unallocated',
    purpose: 'Signals resourcing gaps or upcoming availability',
  },
}

// See FSD §7.1 — utilization color thresholds
function utilizationColor(pct: number): { text: string; label: string } {
  if (pct >= 70) return { text: '#16a34a', label: 'Healthy' }
  if (pct >= 50) return { text: '#ea580c', label: 'Below target' }
  return { text: '#ef4444', label: 'Critical' }
}

function daysClass(days: number): string {
  if (days <= 7) return 'text-[#ef4444] font-semibold'
  if (days <= 14) return 'text-[#f59e0b] font-semibold'
  return 'text-[#6b7280] font-semibold'
}

function KpiCard({
  label, value, sub, detail, accentClass, textClass, tooltip,
}: {
  label: string; value: string; sub?: React.ReactNode; detail?: string
  accentClass: string; textClass: string; tooltip: InfoTooltipContent
}) {
  return (
    <div
      className="relative rounded-xl border border-[#E8EAF6] bg-white p-5"
      style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
    >
      <div className={`absolute top-0 left-0 right-0 h-[3px] rounded-t-xl ${accentClass}`} />
      <div className="flex items-center gap-1.5 text-[12px] font-semibold uppercase tracking-wide text-[#7C85C0] mb-2">
        {label}
        <InfoTooltip content={tooltip} />
      </div>
      <div className={`text-[32px] font-extrabold leading-none ${textClass}`}>
        {value}
      </div>
      {sub && <div className="text-[12px] text-[#6b7280] mt-1.5 flex items-center gap-1">{sub}</div>}
      {detail && <div className="text-[11px] text-[#7C85C0] mt-1">{detail}</div>}
    </div>
  )
}

function ReleaseList({ releases }: { releases: UpcomingRelease[] }) {
  if (releases.length === 0) return <div className="text-[13px] text-[#6b7280] text-center py-6">No upcoming releases</div>

  return (
    <div className="divide-y divide-[#E8EAF6]">
      {releases.map((r, i) => (
        <div key={i} className="flex items-center justify-between py-2.5">
          <div>
            <div className="text-[13px] font-semibold text-[#1e1b4b]">{r.resource_name}</div>
            <div className="text-[12px] text-[#6b7280]">{r.project_name}</div>
          </div>
          <div className="text-right">
            <div className="text-[12px] text-[#7C85C0]">{new Date(r.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
            <div className={`text-[12px] ${daysClass(r.days_remaining)}`}>{r.days_remaining} days left</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function OverdueMilestoneList({ milestones, onClickMilestone }: { milestones: OverdueMilestone[]; onClickMilestone: (m: OverdueMilestone) => void }) {
  if (milestones.length === 0) return <div className="text-[13px] text-[#6b7280] text-center py-6">No delivery delays</div>

  return (
    <div className="divide-y divide-[#E8EAF6]">
      {milestones.map((m) => (
        <div
          key={m.id}
          className="flex items-center justify-between py-2.5 px-1 cursor-pointer hover:bg-[#F0F1FA] rounded transition-colors"
          onClick={() => onClickMilestone(m)}
        >
          <div>
            <div className="text-[13px] font-semibold text-[#1e1b4b]">{m.name}</div>
            <div className="text-[12px] text-[#6b7280]">{m.project_name}</div>
          </div>
          <div className="text-[12px] font-semibold text-[#ef4444]">{m.days_overdue}d overdue</div>
        </div>
      ))}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-[#E8EAF6]" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div className="h-64 rounded-xl bg-[#E8EAF6]" />
        <div className="h-64 rounded-xl bg-[#E8EAF6]" />
      </div>
    </div>
  )
}

export function DMDashboard() {
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'dm'],
    queryFn: fetchDMDashboard,
  })

  if (isLoading) return <LoadingSkeleton />
  if (error) return <div className="text-center py-12 text-[#ef4444]">Failed to load dashboard</div>
  if (!data) return null

  const util = utilizationColor(data.portfolio_utilization_pct)

  return (
    <div>
      {/* KPI Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard
          label="Portfolio Utilization"
          value={`${data.portfolio_utilization_pct}%`}
          sub={<span style={{ color: util.text }}>{util.label}</span>}
          detail={`${data.resource_count} resources across ${data.active_project_count} projects`}
          accentClass="bg-gradient-to-r from-[#2B3990] to-[#4A5BB5]"
          textClass="text-[#2B3990]"
          tooltip={KPI_TOOLTIPS.portfolioUtilization}
        />
        <KpiCard
          label="Portfolio Revenue"
          value={formatInr(data.projected_revenue_inr)}
          sub="Projected from active assignments"
          accentClass="bg-gradient-to-r from-[#0d9488] to-[#2dd4bf]"
          textClass="text-[#0d9488]"
          tooltip={KPI_TOOLTIPS.portfolioRevenue}
        />
        <KpiCard
          label="Portfolio Cost"
          value={formatInr(data.total_cost_inr)}
          sub={
            data.resource_cost_inr !== null || data.non_human_cost_inr !== null
              ? `Resource: ${formatInr(data.resource_cost_inr)} · Non-Human: ${formatInr(data.non_human_cost_inr)}`
              : undefined
          }
          accentClass="bg-gradient-to-r from-[#ea580c] to-[#f59e0b]"
          textClass="text-[#ea580c]"
          tooltip={KPI_TOOLTIPS.portfolioCost}
        />
        <KpiCard
          label="Delivery Delays"
          value={String(data.delivery_delays_count)}
          sub={data.delivery_delays_count > 0 ? <span className="text-[#ef4444]">milestones overdue</span> : <span className="text-[#16a34a]">On track</span>}
          accentClass="bg-gradient-to-r from-[#FF4B2B] to-[#FF7043]"
          textClass={data.delivery_delays_count > 0 ? 'text-[#FF4B2B]' : 'text-[#16a34a]'}
          tooltip={KPI_TOOLTIPS.deliveryDelays}
        />
        <KpiCard
          label="Active Projects"
          value={String(data.active_project_count)}
          accentClass="bg-gradient-to-r from-[#16a34a] to-[#22c55e]"
          textClass="text-[#16a34a]"
          tooltip={KPI_TOOLTIPS.activeProjects}
        />
        <KpiCard
          label="Bench (Portfolio)"
          value={String(data.bench_count)}
          sub={data.bench_count > 0 ? <span className="text-[#ea580c]">resources unallocated</span> : 'All resources allocated'}
          accentClass="bg-gradient-to-r from-[#7c3aed] to-[#a78bfa]"
          textClass="text-[#7c3aed]"
          tooltip={KPI_TOOLTIPS.benchCount}
        />
      </div>

      {/* Margin summary — only when available */}
      {data.projected_margin_inr !== null && (
        <div
          className="mb-6 rounded-xl border border-[#E8EAF6] bg-white p-5"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="flex items-center gap-8">
            <div>
              <div className="text-[12px] font-semibold uppercase tracking-wide text-[#7C85C0] mb-1">Projected Margin</div>
              <div className="text-[24px] font-extrabold text-[#16a34a]">
                {formatInr(data.projected_margin_inr)}
                {data.projected_margin_pct !== null && (
                  <span className="text-[14px] font-bold ml-2">({data.projected_margin_pct.toFixed(1)}%)</span>
                )}
              </div>
            </div>
            <div className="h-10 w-px bg-[#E8EAF6]" />
            <div>
              <div className="text-[12px] font-semibold uppercase tracking-wide text-[#7C85C0] mb-1">Revenue vs Cost</div>
              <div className="text-[14px] text-[#1e1b4b]">
                Revenue: {formatInr(data.projected_revenue_inr)} · Cost: {formatInr(data.total_cost_inr)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delivery Delays + Upcoming Releases */}
      <div className="grid grid-cols-[1fr_1fr] gap-6 mb-6">
        {/* Delivery Delays */}
        <div
          className="rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="px-5 py-3.5 border-b border-[#E8EAF6] flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-[#1e1b4b]">Delivery Delays</h3>
            {data.delivery_delays_count > 0 && (
              <span className="inline-flex items-center rounded-full bg-[#fee2e2] px-2.5 py-0.5 text-[12px] font-bold text-[#991b1b]">
                {data.delivery_delays_count}
              </span>
            )}
          </div>
          <div className="px-5 py-2">
            <OverdueMilestoneList
              milestones={data.delivery_delays ?? []}
              onClickMilestone={(m) => navigate(`/projects/${m.project_id}?tab=milestones`)}
            />
          </div>
        </div>

        {/* Upcoming Releases */}
        <div
          className="rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="px-5 py-3.5 border-b border-[#E8EAF6] flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-[#1e1b4b]">Upcoming Releases (30 Days)</h3>
            <span className="text-[12px] text-[#7C85C0]">{data.upcoming_releases_30d.length} assignments ending</span>
          </div>
          <div className="px-5 py-2">
            <ReleaseList releases={data.upcoming_releases_30d} />
          </div>
        </div>
      </div>
    </div>
  )
}
