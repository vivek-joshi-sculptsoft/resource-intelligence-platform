import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { InfoTooltip, type InfoTooltipContent } from '../../../shared/components/InfoTooltip'
import { fetchCompanyDashboard, type BenchResource, type OverdueMilestone, type UpcomingRelease } from '../api'

function formatInr(val: number | null): string {
  if (val === null) return '—'
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

// See modules/07-utilization-dashboards/SCREENS.md — Info Tooltips; formulas per shared/BUSINESS-RULES.md §7
const KPI_TOOLTIPS: Record<string, InfoTooltipContent> = {
  billableUtilization: {
    formula: 'SUM(billable_pct) for non-shadow ACTIVE assignments / (active_resource_count × 100) × 100',
    meaning: 'Share of total available capacity that is currently billed to clients',
    purpose: 'Core revenue-generating efficiency metric; low values mean idle/non-billable capacity',
  },
  benchCount: {
    formula: 'COUNT(resources WHERE 0 ACTIVE assignments)',
    meaning: 'Number of resources with no active project allocation',
    purpose: 'Drives bench cost exposure and signals resourcing/sales gaps',
  },
  activeProjects: {
    formula: 'COUNT(projects WHERE status = ACTIVE) GROUP BY type',
    meaning: 'Number of currently active engagements, split by FP / T&M / Onboarding',
    purpose: 'Indicates current delivery load and engagement mix',
  },
  activeResources: {
    formula: 'COUNT(resources WHERE is_active = true), with allocated/bench breakdown',
    meaning: 'Total headcount currently available for assignment',
    purpose: 'Denominator for utilization and capacity-planning metrics',
  },
  shadowAllocation: {
    formula: 'COUNT(assignments WHERE is_shadow = true); allocation % = SUM(billability_pct) for shadow assignments',
    meaning: 'Number of shadow (non-billable) assignments and their share of total allocation',
    purpose: 'Shadow resources add cost but contribute no revenue — high values signal hidden cost exposure',
  },
}

// See FSD §7.1 — Company utilization color thresholds
function utilizationColor(pct: number): { text: string; gradient: string; label: string } {
  if (pct >= 70) return { text: '#16a34a', gradient: 'linear-gradient(90deg, #16a34a, #22c55e)', label: 'high' }
  if (pct >= 50) return { text: '#ea580c', gradient: 'linear-gradient(90deg, #f59e0b, #fbbf24)', label: 'medium' }
  return { text: '#ef4444', gradient: 'linear-gradient(90deg, #ef4444, #f87171)', label: 'low' }
}

function daysClass(days: number): string {
  if (days <= 7) return 'text-[#ef4444] font-semibold'
  if (days <= 14) return 'text-[#f59e0b] font-semibold'
  return 'text-[#6b7280] font-semibold'
}

const PROJECT_TYPE_LABELS: Record<string, string> = {
  FIXED_PRICE: 'FP',
  TIME_AND_MATERIAL: 'T&M',
  CLIENT_ONBOARDING: 'Onboarding',
}

function KpiCard({
  label, value, sub, detail, accentClass, textClass, phase2, tooltip,
}: {
  label: string; value: string; sub?: React.ReactNode; detail?: string
  accentClass: string; textClass: string; phase2?: boolean; tooltip: InfoTooltipContent
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
        {phase2 && (
          <span className="ml-2 inline-flex items-center gap-1 rounded-md border border-dashed border-[#D1D5DB] bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-tight">
            Phase 2
          </span>
        )}
      </div>
      <div className={`text-[32px] font-extrabold leading-none ${textClass}`} style={phase2 ? { opacity: 0.4 } : undefined}>
        {value}
      </div>
      {sub && <div className="text-[12px] text-[#6b7280] mt-1.5 flex items-center gap-1" style={phase2 ? { opacity: 0.4 } : undefined}>{sub}</div>}
      {detail && <div className="text-[11px] text-[#7C85C0] mt-1">{detail}</div>}
    </div>
  )
}

function BenchList({ resources, onClickResource }: { resources: BenchResource[]; onClickResource: (id: string) => void }) {
  if (resources.length === 0) return <div className="text-[13px] text-[#6b7280] text-center py-6">No resources on bench</div>

  return (
    <div className="divide-y divide-[#E8EAF6]">
      {resources.map((r) => (
        <div
          key={r.id}
          className="flex items-center justify-between py-2.5 px-1 cursor-pointer hover:bg-[#F0F1FA] rounded transition-colors"
          onClick={() => onClickResource(r.id)}
        >
          <div>
            <div className="text-[13px] font-semibold text-[#1e1b4b]">{r.name}</div>
            <div className="text-[12px] text-[#6b7280]">{r.designation}</div>
          </div>
          <div className="text-[12px] font-semibold text-[#ea580c]">{r.days_on_bench}d</div>
        </div>
      ))}
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
  if (milestones.length === 0) return <div className="text-[13px] text-[#6b7280] text-center py-6">No overdue milestones</div>

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

export function CompanyDashboard() {
  const navigate = useNavigate()
  const [benchExpanded, setBenchExpanded] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'company'],
    queryFn: fetchCompanyDashboard,
  })

  if (isLoading) return <LoadingSkeleton />
  if (error) return <div className="text-center py-12 text-[#ef4444]">Failed to load dashboard</div>
  if (!data) return null

  const util = utilizationColor(data.billable_utilization_pct)
  const typeBreakdown = Object.entries(data.active_projects_by_type)
    .map(([k, v]) => `${PROJECT_TYPE_LABELS[k] || k}: ${v}`)
    .join(' · ')

  return (
    <div>
      {/* KPI Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Billable Utilization"
          value={`${data.billable_utilization_pct}%`}
          sub={<span style={{ color: util.text }}>{util.label === 'high' ? 'Healthy' : util.label === 'medium' ? 'Below target' : 'Critical'}</span>}
          detail={`${data.total_active_resources - data.bench_count} of ${data.total_active_resources} resources billable`}
          accentClass="bg-gradient-to-r from-[#2B3990] to-[#4A5BB5]"
          textClass="text-[#2B3990]"
          tooltip={KPI_TOOLTIPS.billableUtilization}
        />
        <KpiCard
          label="Bench Count"
          value={String(data.bench_count)}
          sub={
            data.bench_count > 0 ? (
              <button onClick={() => setBenchExpanded(!benchExpanded)} className="text-[#2B3990] underline cursor-pointer text-[12px]">
                {benchExpanded ? 'Hide details' : 'View details'}
              </button>
            ) : undefined
          }
          detail={data.total_bench_cost_monthly !== null ? `${formatInr(data.total_bench_cost_monthly)}/mo bench cost` : undefined}
          accentClass="bg-gradient-to-r from-[#ea580c] to-[#f59e0b]"
          textClass="text-[#ea580c]"
          tooltip={KPI_TOOLTIPS.benchCount}
        />
        <KpiCard
          label="Active Projects"
          value={String(data.active_project_count)}
          sub={typeBreakdown || '—'}
          accentClass="bg-gradient-to-r from-[#16a34a] to-[#22c55e]"
          textClass="text-[#16a34a]"
          tooltip={KPI_TOOLTIPS.activeProjects}
        />
        <KpiCard
          label="Active Resources"
          value={String(data.total_active_resources)}
          sub={`${data.total_active_resources - data.bench_count} allocated · ${data.bench_count} on bench`}
          accentClass="bg-gradient-to-r from-[#7c3aed] to-[#a78bfa]"
          textClass="text-[#7c3aed]"
          tooltip={KPI_TOOLTIPS.activeResources}
        />
      </div>

      {/* Expandable Bench List */}
      {benchExpanded && data.bench_resources.length > 0 && (
        <div
          className="mb-6 rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="px-5 py-3.5 border-b border-[#E8EAF6] flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-[#1e1b4b]">Bench Resources</h3>
            <span className="text-[12px] text-[#7C85C0]">{data.bench_resources.length} resources</span>
          </div>
          <div className="px-5 py-2">
            <BenchList resources={data.bench_resources} onClickResource={(id) => navigate(`/resources/${id}`)} />
          </div>
        </div>
      )}

      {/* Overdue Milestones — See VRIP-106. Two-col layout returns in VRIP-129 when
          Top 5 Projects by Team Size fills the slot Revenue vs Cost used to occupy. */}
      <div className="mb-6">
        <div
          className="rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="px-5 py-3.5 border-b border-[#E8EAF6] flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-[#1e1b4b]">Overdue Milestones</h3>
            {data.overdue_milestones_count !== null && data.overdue_milestones_count > 0 && (
              <span className="inline-flex items-center rounded-full bg-[#fee2e2] px-2.5 py-0.5 text-[12px] font-bold text-[#991b1b]">
                {data.overdue_milestones_count}
              </span>
            )}
          </div>
          <div className="px-5 py-2">
            <OverdueMilestoneList
              milestones={data.overdue_milestones ?? []}
              onClickMilestone={(m) => navigate(`/projects/${m.project_id}?tab=milestones`)}
            />
          </div>
        </div>
      </div>

      {/* Shadow + Releases row */}
      <div className="grid grid-cols-[1.2fr_1fr] gap-6 mb-6">
        {/* Shadow Allocation Card */}
        <div
          className="rounded-xl border border-[#E8EAF6] bg-white"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06)' }}
        >
          <div className="px-5 py-3.5 border-b border-[#E8EAF6] flex items-center gap-1.5">
            <h3 className="text-[15px] font-bold text-[#1e1b4b]">Shadow Allocation</h3>
            <InfoTooltip content={KPI_TOOLTIPS.shadowAllocation} />
          </div>
          <div className="p-5">
            {data.shadow_count === 0 ? (
              <div className="text-[13px] text-[#6b7280] text-center py-6">No shadow assignments</div>
            ) : (
              <div className="flex items-center gap-8">
                <div>
                  <div className="text-[28px] font-extrabold text-[#7c3aed]">{data.shadow_count}</div>
                  <div className="text-[12px] text-[#6b7280]">shadow assignments</div>
                </div>
                <div>
                  <div className="text-[28px] font-extrabold text-[#7c3aed]">{data.shadow_total_allocation_pct}%</div>
                  <div className="text-[12px] text-[#6b7280]">total allocation</div>
                </div>
              </div>
            )}
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
