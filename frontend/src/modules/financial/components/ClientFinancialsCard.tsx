// See FSD §7.2-§7.5 — Client-level financial aggregation (Module 08 / VRIP-108)
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { fetchClientFinancials } from '../api'
import { InfoTooltip, type InfoTooltipContent } from '../../../shared/components/InfoTooltip'

const TOOLTIPS: Record<string, InfoTooltipContent> = {
  totalBilling: {
    formula: 'SUM(per-project projected revenue) across all the client\'s active projects',
    meaning: 'Total projected monthly billing for this client',
    purpose: 'Top-line revenue indicator for the client relationship',
  },
  totalCost: {
    formula: 'SUM(Resource Cost + Non-Human Cost) across all the client\'s projects',
    meaning: 'Total monthly cost of delivering for this client',
    purpose: 'Cost baseline for measuring client profitability',
  },
  margin: {
    formula: 'Total Projected Revenue (INR) − Total Cost',
    meaning: 'Aggregate projected profitability for this client',
    purpose: 'Bottom-line indicator of whether this client relationship is profitable',
  },
}

function formatInr(val: number | null): string {
  if (val === null) return '—'
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function marginColor(pct: number | null): { bg: string; fg: string; label: string } {
  if (pct === null) return { bg: '#F5F6FC', fg: '#6b7280', label: 'Unknown' }
  if (pct >= 20) return { bg: '#dcfce7', fg: '#166534', label: 'Healthy' }
  if (pct >= 0) return { bg: '#fef3c7', fg: '#92400e', label: 'Thin' }
  return { bg: '#fecaca', fg: '#991b1b', label: 'Negative' }
}

interface ClientFinancialsCardProps {
  clientId: string
}

export function ClientFinancialsCard({ clientId }: ClientFinancialsCardProps) {
  const navigate = useNavigate()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['client-financials', clientId],
    queryFn: () => fetchClientFinancials(clientId),
  })

  if (isLoading) {
    return (
      <div className="mb-5 rounded-xl p-6 text-center text-[13.5px]" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06)', color: '#7C85C0' }}>
        Loading financial data...
      </div>
    )
  }

  if (isError) {
    const status = (error as any)?.response?.status
    if (status === 403) {
      // See ACCESS-MATRIX.md — no financial visibility for this role; not an error state
      return null
    }
    return (
      <div className="mb-5 rounded-xl p-6 text-center text-[13.5px]" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06)', color: '#ef4444' }}>
        Failed to load financial data.
      </div>
    )
  }

  if (!data) return null

  const badge = marginColor(data.projected_margin_pct)

  const kpiCards = [
    { label: 'Total Billing (INR)', value: formatInr(data.total_projected_revenue_inr), sub: 'Projected monthly', accentTop: 'linear-gradient(90deg, #059669, #34d399)', tooltip: TOOLTIPS.totalBilling },
    { label: 'Total Cost (INR)', value: formatInr(data.total_cost_inr), sub: `Resource: ${formatInr(data.total_resource_cost_inr)} · Non-Human: ${formatInr(data.total_non_human_cost_inr)}`, accentTop: 'linear-gradient(90deg, #ea580c, #f59e0b)', tooltip: TOOLTIPS.totalCost },
    {
      label: 'Aggregate Margin',
      value: data.projected_margin_pct === null ? '—' : `${data.projected_margin_pct.toFixed(1)}%`,
      sub: formatInr(data.projected_margin_inr),
      accentTop: 'linear-gradient(90deg, #2B3990, #4A5BB5)',
      badge,
      tooltip: TOOLTIPS.margin,
    },
  ]

  return (
    <div className="mb-5">
      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        {kpiCards.map((card) => (
          <div key={card.label} className="relative rounded-xl border border-[#E8EAF6] bg-white p-5" style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
            <div className="absolute top-0 left-0 right-0 h-[3px] rounded-t-xl" style={{ background: card.accentTop }} />
            <div className="flex items-center gap-1.5 text-[12px] font-semibold uppercase tracking-wide text-[#7C85C0] mb-2">
              {card.label}
              <InfoTooltip content={card.tooltip} />
            </div>
            <div className="text-[24px] font-extrabold leading-none text-[#1e1b4b]">{card.value}</div>
            {card.sub && <div className="text-[12px] text-[#6b7280] mt-1.5">{card.sub}</div>}
            {card.badge && (
              <div className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold mt-2" style={{ background: card.badge.bg, color: card.badge.fg }}>
                ● {card.badge.label}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Per-Project Financial Breakdown */}
      {data.per_project.length > 0 && (
        <div className="rounded-xl" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="px-6 pt-5 pb-3 flex items-center justify-between">
            <h2 className="text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Financial Breakdown by Project</h2>
            <span className="text-[12px]" style={{ color: '#7C85C0' }}>{data.per_project.length} project{data.per_project.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13.5px]">
              <thead>
                <tr>
                  {['Project Name', 'Total Cost', 'Projected Revenue', 'Actual Revenue'].map((h, i) => (
                    <th key={h} className={`whitespace-nowrap px-4 py-[11px] text-[12px] font-semibold uppercase tracking-wide first:pl-6 ${i > 0 ? 'text-right' : ''}`}
                      style={{ background: '#F0F1FA', color: '#7C85C0', borderBottom: '1px solid #E8EAF6' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.per_project.map((p) => (
                  <tr key={p.project_id} className="cursor-pointer transition-colors"
                    style={{ borderBottom: '1px solid #E8EAF6' }}
                    onClick={() => navigate(`/projects/${p.project_id}?tab=financials`)}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#F0F1FA' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = '#fff' }}>
                    <td className="whitespace-nowrap px-4 py-[12px] pl-6 font-semibold" style={{ color: '#2B3990' }}>{p.project_name}</td>
                    <td className="whitespace-nowrap px-4 py-[12px] text-right" style={{ color: '#1e1b4b' }}>{formatInr(p.total_cost_inr)}</td>
                    <td className="whitespace-nowrap px-4 py-[12px] text-right" style={{ color: '#1e1b4b' }}>{formatInr(p.projected_revenue_inr)}</td>
                    <td className="whitespace-nowrap px-4 py-[12px] text-right" style={{ color: '#1e1b4b' }}>{formatInr(p.actual_revenue_inr)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
