// See FSD §7.2-§7.5 — Project Financials tab (Module 08)
import type { CSSProperties } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchProjectFinancials } from '../api'
import { fetchCostSummary } from '../../nonhuman_costs/api'

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

const cardStyle: CSSProperties = {
  background: '#fff',
  borderRadius: 12,
  boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
  border: '1px solid #E8EAF6',
  overflow: 'hidden',
}

const sectionHeaderStyle: CSSProperties = {
  padding: '16px 20px',
  borderBottom: '1px solid #E8EAF6',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  background: 'linear-gradient(135deg, rgba(43,57,144,0.03), rgba(74,91,181,0.02))',
}

interface ProjectFinancialsTabProps {
  projectId: string
}

export function ProjectFinancialsTab({ projectId }: ProjectFinancialsTabProps) {
  const { data: financials, isLoading, isError, error } = useQuery({
    queryKey: ['project-financials', projectId],
    queryFn: () => fetchProjectFinancials(projectId),
  })

  const { data: nhcSummary } = useQuery({
    queryKey: ['project-costs-summary', projectId],
    queryFn: () => fetchCostSummary(projectId),
  })

  if (isLoading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#6b7280', fontSize: 14 }}>Loading...</div>
  }

  if (isError) {
    const status = (error as any)?.response?.status
    if (status === 403) {
      return (
        <div style={{ ...cardStyle, textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>
            Financial Data Restricted
          </div>
          <div style={{ fontSize: 14, color: '#7C85C0' }}>
            You do not have permission to view financials for this project.
          </div>
        </div>
      )
    }
    return <div style={{ padding: 40, textAlign: 'center', color: '#ef4444', fontSize: 14 }}>Failed to load financial data.</div>
  }

  if (!financials) return null

  const hasAnyCost = financials.total_cost_inr !== null || financials.resource_cost_breakdown.length > 0
  if (!hasAnyCost) {
    return (
      <div style={{ ...cardStyle, textAlign: 'center', padding: '60px 20px' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📈</div>
        <div style={{ fontSize: 16, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>
          Financial data is not yet available
        </div>
        <div style={{ fontSize: 14, color: '#7C85C0', maxWidth: 400, margin: '0 auto' }}>
          Ensure resources have loaded costs and assignments have billing rates to see project financial analysis.
        </div>
      </div>
    )
  }

  const missingCount = financials.missing_costs.length + financials.missing_rates.length
  const badge = marginColor(financials.projected_margin_pct)

  const kpiCards = [
    { label: 'Total Cost', value: formatInr(financials.total_cost_inr), sub: 'Resource + Non-Human Costs', accentTop: 'linear-gradient(90deg, #2B3990, #4A5BB5)' },
    { label: 'Projected Revenue', value: formatInr(financials.projected_revenue_inr), sub: 'Based on contract value', accentTop: 'linear-gradient(90deg, #059669, #34d399)' },
    { label: 'Actual Revenue', value: formatInr(financials.actual_revenue_inr), sub: 'Approved + Paid invoices', accentTop: 'linear-gradient(90deg, #f59e0b, #fcd34d)' },
    {
      label: 'Projected Margin',
      value: financials.projected_margin_pct === null ? '—' : `${financials.projected_margin_pct.toFixed(1)}%`,
      sub: null,
      accentTop: 'linear-gradient(90deg, #22c55e, #86efac)',
      badge,
    },
  ]

  return (
    <div>
      {missingCount > 0 && (
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', marginBottom: 20,
            background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 8, fontSize: 13, color: '#92400e',
          }}
        >
          ⚠️{' '}
          <span>
            {missingCount} resource{missingCount !== 1 ? 's are' : ' is'} missing loaded cost or billing rate data.
            Financial calculations may be incomplete.
          </span>
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {kpiCards.map((card) => (
          <div key={card.label} style={{ ...cardStyle, padding: 20, position: 'relative' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: card.accentTop }} />
            <div style={{ fontSize: 12, fontWeight: 600, color: '#7C85C0', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>
              {card.label}
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#1e1b4b' }}>{card.value}</div>
            {card.sub && <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{card.sub}</div>}
            {card.badge && (
              <div
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px',
                  borderRadius: 20, fontSize: 13, fontWeight: 600, marginTop: 6,
                  background: card.badge.bg, color: card.badge.fg,
                }}
              >
                ● {card.badge.label}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Resource Cost Breakdown */}
      <div style={{ ...cardStyle, marginBottom: 24 }}>
        <div style={sectionHeaderStyle}>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b' }}>Resource Cost Breakdown</div>
          <span style={{ fontSize: 13, color: '#7C85C0' }}>
            {financials.resource_cost_breakdown.length} assigned resource{financials.resource_cost_breakdown.length !== 1 ? 's' : ''}
          </span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Resource', 'Designation', 'Allocation %', 'Loaded Cost / Month', 'Monthly Cost Contribution'].map((h, i) => (
                <th
                  key={h}
                  style={{
                    padding: '12px 16px', textAlign: i >= 2 ? 'right' : 'left', fontSize: 12, fontWeight: 600,
                    color: '#7C85C0', textTransform: 'uppercase', letterSpacing: 0.5,
                    background: '#F5F6FC', borderBottom: '1px solid #E8EAF6',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {financials.resource_cost_breakdown.map((r) => (
              <tr key={r.resource_name} style={{ borderBottom: '1px solid #E8EAF6' }}>
                <td style={{ padding: '12px 16px', fontSize: 14, fontWeight: 600, color: '#1e1b4b' }}>{r.resource_name}</td>
                <td style={{ padding: '12px 16px', fontSize: 14, color: '#1e1b4b' }}>{r.resource_designation}</td>
                <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right', color: '#1e1b4b' }}>{r.allocation_pct}%</td>
                <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right', color: '#1e1b4b' }}>
                  {formatInr(r.loaded_cost_monthly)}
                </td>
                <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right', color: '#1e1b4b' }}>
                  {formatInr(r.cost_contribution_inr)}
                </td>
              </tr>
            ))}
            <tr style={{ background: '#F5F6FC', fontWeight: 700 }}>
              <td colSpan={2} style={{ padding: '12px 16px', fontSize: 14 }}>Total Resource Cost</td>
              <td style={{ padding: '12px 16px', textAlign: 'right' }}>—</td>
              <td style={{ padding: '12px 16px', textAlign: 'right' }}>—</td>
              <td style={{ padding: '12px 16px', textAlign: 'right', fontSize: 14, color: '#2B3990' }}>
                {formatInr(financials.resource_cost_inr)} /mo
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Two Column: Non-Human Costs + Revenue vs Cost */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b' }}>Non-Human Costs</div>
          </div>
          {nhcSummary ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, padding: 20 }}>
                <div>
                  <div style={{ fontSize: 12, color: '#7C85C0', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                    One-Time Costs
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e1b4b', marginTop: 4 }}>
                    {formatInr(nhcSummary.one_time_inr)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#7C85C0', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                    Recurring (Monthly)
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e1b4b', marginTop: 4 }}>
                    {formatInr(nhcSummary.recurring_monthly_inr)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#7C85C0', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                    Total NHC (To Date)
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e1b4b', marginTop: 4 }}>
                    {formatInr(nhcSummary.total_inr)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#7C85C0', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                    NHC Categories
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#1e1b4b', marginTop: 4 }}>
                    {Object.keys(nhcSummary.by_category).length > 0 ? Object.keys(nhcSummary.by_category).join(', ') : '—'}
                  </div>
                </div>
              </div>
              <div style={{ padding: '0 20px 16px' }}>
                <a
                  href={`/projects/${projectId}?tab=costs`}
                  style={{ fontSize: 13, color: '#2B3990', fontWeight: 500, textDecoration: 'none' }}
                >
                  View detailed non-human costs →
                </a>
              </div>
            </>
          ) : (
            <div style={{ padding: 20, fontSize: 13, color: '#7C85C0' }}>No non-human cost data.</div>
          )}
        </div>

        <div style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b' }}>Revenue vs Cost</div>
          </div>
          <div style={{ padding: 20 }}>
            {[
              { label: 'Total Cost', value: financials.total_cost_inr, color: 'linear-gradient(90deg, #2B3990, #4A5BB5)' },
              { label: 'Projected Revenue', value: financials.projected_revenue_inr, color: 'linear-gradient(90deg, #059669, #34d399)' },
              { label: 'Actual Revenue', value: financials.actual_revenue_inr, color: 'linear-gradient(90deg, #f59e0b, #fcd34d)' },
            ].map((bar) => {
              const max = Math.max(
                financials.total_cost_inr ?? 0,
                financials.projected_revenue_inr ?? 0,
                financials.actual_revenue_inr ?? 0,
                1,
              )
              const width = bar.value === null ? 0 : Math.min(100, (bar.value / max) * 100)
              return (
                <div key={bar.label} style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, color: '#1e1b4b' }}>{bar.label}</span>
                    <span style={{ color: '#6b7280' }}>{formatInr(bar.value)}</span>
                  </div>
                  <div style={{ height: 24, background: '#F0F1FA', borderRadius: 12, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${width}%`, background: bar.color, borderRadius: 12, transition: 'width 0.4s' }} />
                  </div>
                </div>
              )
            })}
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #E8EAF6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ fontWeight: 700, color: '#1e1b4b' }}>Projected Margin</span>
                <span style={{ fontWeight: 700, color: '#22c55e' }}>
                  {formatInr(financials.projected_margin_inr)}
                  {financials.projected_margin_pct !== null && ` (${financials.projected_margin_pct.toFixed(1)}%)`}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginTop: 8 }}>
                <span style={{ color: '#1e1b4b' }}>Actual Margin (to date)</span>
                <span style={{ color: '#f59e0b' }}>
                  {formatInr(financials.actual_margin_inr)}
                  {financials.actual_margin_pct !== null && ` (${financials.actual_margin_pct.toFixed(1)}%)`}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
