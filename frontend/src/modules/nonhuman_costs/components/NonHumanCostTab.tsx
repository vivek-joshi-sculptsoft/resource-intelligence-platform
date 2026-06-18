// See FSD §2.10 — NonHumanCost tab within Project Detail
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { fetchCosts, fetchCostSummary, deleteCost, type CostEntry } from '../api'
import { CostFormModal } from './CostFormModal'
import { ConfirmDialog, SearchableSelect } from '../../../shared/components'

const CATEGORY_LABELS: Record<string, string> = {
  AI_TOOLS: 'AI Tools',
  CLOUD_INFRA: 'Cloud Infra',
  DEVICES: 'Devices',
  THIRD_PARTY_LICENSE: 'Third-Party License',
  OTHER: 'Other',
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatInr(val: number): string {
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatAmount(amount: number, currency: string): string {
  const symbols: Record<string, string> = { INR: '₹', USD: '$', EUR: '€', GBP: '£' }
  const sym = symbols[currency] ?? ''
  return `${sym}${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

interface NonHumanCostTabProps {
  projectId: string
  canEdit: boolean
}

export function NonHumanCostTab({ projectId, canEdit }: NonHumanCostTabProps) {
  const queryClient = useQueryClient()

  const [categoryFilter, setCategoryFilter] = useState('')
  const [recurringFilter, setRecurringFilter] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingCost, setEditingCost] = useState<CostEntry | null>(null)
  const [deletingCost, setDeletingCost] = useState<CostEntry | null>(null)

  const { data: costsData, isLoading } = useQuery({
    queryKey: ['project-costs', projectId, categoryFilter, recurringFilter],
    queryFn: () =>
      fetchCosts(projectId, {
        category: categoryFilter || undefined,
        is_recurring: recurringFilter || undefined,
        limit: 100,
      }),
  })

  const { data: summary } = useQuery({
    queryKey: ['project-costs-summary', projectId],
    queryFn: () => fetchCostSummary(projectId),
  })

  const deleteMutation = useMutation({
    mutationFn: (costId: string) => deleteCost(projectId, costId),
    onSuccess: () => {
      toast.success('Cost deleted')
      queryClient.invalidateQueries({ queryKey: ['project-costs', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-costs-summary', projectId] })
      setDeletingCost(null)
    },
    onError: () => {
      toast.error('Failed to delete cost')
      setDeletingCost(null)
    },
  })

  const costs: CostEntry[] = costsData?.data ?? []

  function openAdd() {
    setEditingCost(null)
    setModalOpen(true)
  }

  function openEdit(c: CostEntry) {
    setEditingCost(c)
    setModalOpen(true)
  }

  return (
    <div>
      {/* Summary Cards */}
      {summary && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
          {[
            { label: 'Total Cost (INR)', value: formatInr(summary.total_inr), accent: false },
            { label: 'One-Time Total', value: formatInr(summary.one_time_inr), accent: false },
            { label: 'Recurring Monthly', value: formatInr(summary.recurring_monthly_inr), accent: true },
            { label: 'Cost Entries', value: String(costsData?.total ?? 0), accent: false },
          ].map((card) => (
            <div
              key={card.label}
              style={{
                flex: 1,
                background: '#fff',
                border: '1px solid #E8EAF6',
                borderRadius: 12,
                padding: '14px 20px',
                boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, color: '#7C85C0', marginBottom: 4 }}>
                {card.label}
              </div>
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  color: card.accent ? '#FF4B2B' : '#2B3990',
                }}
              >
                {card.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table Card */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
          border: '1px solid #E8EAF6',
          overflow: 'hidden',
        }}
      >
        {/* Action Bar */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #E8EAF6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <SearchableSelect
              value={categoryFilter}
              onChange={setCategoryFilter}
              options={[
                { value: '', label: 'All Categories' },
                ...Object.entries(CATEGORY_LABELS).map(([v, l]) => ({ value: v, label: l })),
              ]}
              placeholder="All Categories"
              variant="filter"
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#6b7280', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={recurringFilter}
                onChange={(e) => setRecurringFilter(e.target.checked)}
                style={{ width: 16, height: 16, accentColor: '#2B3990' }}
              />
              Recurring only
            </label>
          </div>
          {canEdit && (
            <button
              onClick={openAdd}
              style={{
                background: '#FF4B2B', color: '#fff', border: 'none', padding: '8px 18px',
                borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                display: 'inline-flex', alignItems: 'center', gap: 6,
              }}
            >
              <Plus size={14} /> Add Cost
            </button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#6b7280', fontSize: 14 }}>Loading...</div>
        ) : costs.length === 0 ? (
          <div style={{ padding: '60px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📦</div>
            <h3 style={{ fontSize: 16, color: '#1e1b4b', marginBottom: 6 }}>No costs recorded yet</h3>
            <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>
              Add your first cost entry to start tracking non-human project expenses.
            </p>
            {canEdit && (
              <button
                onClick={openAdd}
                style={{
                  background: '#FF4B2B', color: '#fff', border: 'none', padding: '8px 18px',
                  borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                }}
              >
                <Plus size={14} /> Add Cost
              </button>
            )}
          </div>
        ) : (
          <>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr
                  style={{
                    background: 'linear-gradient(135deg, #2B3990 0%, #4A5BB5 100%)',
                  }}
                >
                  {['Date', 'Description', 'Category', 'Amount', 'Ex. Rate', 'Amount (INR)', 'Recurring', 'Added By', 'Actions'].map(
                    (h, i) => (
                      <th
                        key={h}
                        style={{
                          padding: '12px 16px',
                          textAlign: i >= 3 && i <= 5 ? 'right' : i === 8 ? 'center' : 'left',
                          fontSize: 12,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: 0.5,
                          color: '#fff',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {costs.map((c, idx) => (
                  <tr
                    key={c.id}
                    style={{
                      background: idx % 2 === 1 ? '#F5F6FC' : '#fff',
                      borderBottom: '1px solid #E8EAF6',
                      cursor: canEdit ? 'pointer' : 'default',
                    }}
                    onClick={() => canEdit && openEdit(c)}
                  >
                    <td style={{ padding: '12px 16px', fontSize: 13, whiteSpace: 'nowrap' }}>
                      {formatDate(c.cost_date)}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13, maxWidth: 220 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {c.description}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13 }}>
                      <span
                        style={{
                          display: 'inline-flex', alignItems: 'center', padding: '3px 10px',
                          borderRadius: 12, fontSize: 11, fontWeight: 600,
                          background: '#EEF0FF', color: '#2B3990',
                        }}
                      >
                        {CATEGORY_LABELS[c.category] ?? c.category}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13, textAlign: 'right', whiteSpace: 'nowrap' }}>
                      {formatAmount(c.amount, c.currency)}{' '}
                      <span
                        style={{
                          fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                          background: '#FFF0EC', color: '#FF4B2B',
                        }}
                      >
                        {c.currency}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: '12px 16px', fontSize: 13, textAlign: 'right',
                        color: c.currency === 'INR' ? '#7C85C0' : '#1e1b4b',
                      }}
                    >
                      {Number(c.exchange_rate).toFixed(4)}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 600, textAlign: 'right', color: '#2B3990' }}>
                      {formatInr(c.amount_inr)}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13 }}>
                      {c.is_recurring ? (
                        <span
                          style={{
                            display: 'inline-flex', padding: '3px 10px', borderRadius: 12,
                            fontSize: 11, fontWeight: 600, background: '#FEF3C7', color: '#92400E',
                          }}
                        >
                          Monthly{c.recurring_end_date ? ` until ${formatDate(c.recurring_end_date)}` : ''}
                        </span>
                      ) : (
                        <span
                          style={{
                            display: 'inline-flex', padding: '3px 10px', borderRadius: 12,
                            fontSize: 11, fontWeight: 600, background: '#F0FDF4', color: '#166534',
                          }}
                        >
                          One-time
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 13, color: '#6b7280' }}>
                      {c.created_by?.name ?? '—'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                      {canEdit && (
                        <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
                          <button
                            onClick={() => openEdit(c)}
                            title="Edit"
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              padding: 4, borderRadius: 4, color: '#7C85C0',
                            }}
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => setDeletingCost(c)}
                            title="Delete"
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              padding: 4, borderRadius: 4, color: '#7C85C0',
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ background: '#F5F6FC', borderTop: '2px solid #D6DAF0' }}>
                  <td colSpan={5} style={{ padding: '14px 16px', fontSize: 13, fontWeight: 700, textAlign: 'right' }}>
                    Grand Total (INR)
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: 15, fontWeight: 700, textAlign: 'right', color: '#2B3990' }}>
                    {summary ? formatInr(summary.total_inr) : '—'}
                  </td>
                  <td colSpan={3} />
                </tr>
              </tfoot>
            </table>
          </>
        )}
      </div>

      <CostFormModal
        open={modalOpen}
        projectId={projectId}
        editingCost={editingCost}
        onClose={() => { setModalOpen(false); setEditingCost(null) }}
      />

      <ConfirmDialog
        open={!!deletingCost}
        title="Delete Cost"
        description={`Delete "${deletingCost?.description}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => deletingCost && deleteMutation.mutate(deletingCost.id)}
        onCancel={() => setDeletingCost(null)}
      />
    </div>
  )
}
