// See FSD §6.3 — Invoice list view and status transitions
import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Plus } from 'lucide-react'
import { fetchInvoices, transitionInvoiceStatus, type Invoice, type InvoiceStatus } from '../api'
import { InvoiceFormModal } from './InvoiceFormModal'
import { ConfirmDialog } from '../../../shared/components'
import { useAuthStore } from '../../auth/store'

// See FSD §6.3 — Invoice status transitions (forward-only, Finance only)
const FORWARD_TRANSITIONS: Record<string, InvoiceStatus> = {
  DRAFT: 'SUBMITTED',
  SUBMITTED: 'APPROVED',
  APPROVED: 'PAID',
}

const FORWARD_BUTTON_CONFIG: Record<string, { label: string; className: string }> = {
  DRAFT: { label: 'Submit', className: 'submit' },
  SUBMITTED: { label: 'Approve', className: 'approve' },
  APPROVED: { label: 'Mark Paid', className: 'mark-paid' },
}

const STATUS_BADGE_STYLES: Record<string, { bg: string; color: string }> = {
  DRAFT: { bg: '#f3f4f6', color: '#4b5563' },
  SUBMITTED: { bg: '#dbeafe', color: '#1e40af' },
  APPROVED: { bg: '#dcfce7', color: '#166534' },
  PAID: { bg: '#d1fae5', color: '#065f46' },
}

const ACTION_BTN_STYLES: Record<string, { bg: string; color: string; border: string; hoverBg: string }> = {
  submit: { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe', hoverBg: '#dbeafe' },
  approve: { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', hoverBg: '#dcfce7' },
  'mark-paid': { bg: '#ecfdf5', color: '#047857', border: '#a7f3d0', hoverBg: '#d1fae5' },
  edit: { bg: '#f5f6fc', color: '#2B3990', border: '#D6DAF0', hoverBg: '#F0F1FA' },
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatInr(val: number): string {
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatMoney(val: number, currency: string): string {
  return `${val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency}`
}

interface InvoiceTabProps {
  projectId: string
  projectType: string
  billingCurrency: string
}

export function InvoiceTab({ projectId, projectType, billingCurrency }: InvoiceTabProps) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const roleCode = user?.role.code ?? ''

  const canManage = roleCode === 'FINANCE'

  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null)
  const [confirmTransition, setConfirmTransition] = useState<{
    invoice: Invoice
    targetStatus: InvoiceStatus
    label: string
  } | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['project-invoices', projectId, statusFilter],
    queryFn: () => fetchInvoices(projectId, statusFilter || undefined),
  })

  const transitionMut = useMutation({
    mutationFn: ({ invoiceId, status }: { invoiceId: string; status: InvoiceStatus }) =>
      transitionInvoiceStatus(projectId, invoiceId, status),
    onSuccess: () => {
      toast.success('Invoice status updated')
      queryClient.invalidateQueries({ queryKey: ['project-invoices', projectId] })
      setConfirmTransition(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || 'Failed to update invoice status')
      setConfirmTransition(null)
    },
  })

  const invoices: Invoice[] = data?.data ?? []

  const { totalAmount, paidAmount, paidCount, outstandingAmount, outstandingCount, draftAmount, draftCount } = useMemo(() => {
    const total = invoices.reduce((s, inv) => s + (inv.amount_inr ?? 0), 0)
    const paid = invoices.filter((inv) => inv.status === 'PAID')
    const draft = invoices.filter((inv) => inv.status === 'DRAFT')
    const outstanding = invoices.filter((inv) => inv.status !== 'PAID' && inv.status !== 'DRAFT')
    return {
      totalAmount: total,
      paidAmount: paid.reduce((s, inv) => s + (inv.amount_inr ?? 0), 0),
      paidCount: paid.length,
      outstandingAmount: outstanding.reduce((s, inv) => s + (inv.amount_inr ?? 0), 0),
      outstandingCount: outstanding.length,
      draftAmount: draft.reduce((s, inv) => s + (inv.amount_inr ?? 0), 0),
      draftCount: draft.length,
    }
  }, [invoices])

  function openAdd() {
    setEditingInvoice(null)
    setModalOpen(true)
  }

  function openEdit(inv: Invoice) {
    if (inv.status !== 'DRAFT' || !canManage) return
    setEditingInvoice(inv)
    setModalOpen(true)
  }

  function handleTransition(inv: Invoice) {
    const target = FORWARD_TRANSITIONS[inv.status]
    if (!target) return
    const btn = FORWARD_BUTTON_CONFIG[inv.status]
    setConfirmTransition({ invoice: inv, targetStatus: target, label: btn.label })
  }

  function renderActionBtn(style: string, label: string, onClick: () => void) {
    const s = ACTION_BTN_STYLES[style]
    return (
      <button
        onClick={(e) => { e.stopPropagation(); onClick() }}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
          borderRadius: 8, fontSize: 11, fontWeight: 600, cursor: 'pointer',
          border: `1px solid ${s.border}`, background: s.bg, color: s.color,
          transition: 'background 0.15s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = s.hoverBg)}
        onMouseLeave={(e) => (e.currentTarget.style.background = s.bg)}
      >
        {label}
      </button>
    )
  }

  if (isLoading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#7C85C0', fontSize: 14 }}>Loading invoices...</div>
  }

  if (invoices.length === 0 && !statusFilter) {
    return (
      <>
        <div
          style={{
            background: '#fff', borderRadius: 12,
            boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            border: '1px solid #E8EAF6',
          }}
        >
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b', marginBottom: 8 }}>No invoices yet</div>
            <div style={{ fontSize: 14, color: '#7C85C0', maxWidth: 400, margin: '0 auto' }}>
              Create an invoice to begin tracking revenue. For Fixed Price projects, approve a milestone first.
            </div>
            {canManage && (
              <button
                onClick={openAdd}
                style={{
                  marginTop: 16, background: 'linear-gradient(135deg, #FF4B2B, #E63E1F)',
                  color: '#fff', border: 'none', padding: '8px 18px', borderRadius: 8,
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  boxShadow: '0 2px 6px rgba(255,75,43,0.3)',
                }}
              >
                <Plus size={14} /> Create Invoice
              </button>
            )}
          </div>
        </div>
        <InvoiceFormModal
          open={modalOpen}
          projectId={projectId}
          projectType={projectType}
          billingCurrency={billingCurrency}
          editingInvoice={editingInvoice}
          onClose={() => { setModalOpen(false); setEditingInvoice(null) }}
        />
      </>
    )
  }

  return (
    <div>
      {/* Summary Cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        {[
          { label: 'Total Invoiced', value: formatInr(totalAmount), sub: `${invoices.length} invoices`, accent: 'linear-gradient(90deg, #2B3990, #4A5BB5)' },
          { label: 'Paid', value: formatInr(paidAmount), sub: `${paidCount} invoice${paidCount !== 1 ? 's' : ''}`, accent: 'linear-gradient(90deg, #22c55e, #86efac)' },
          { label: 'Outstanding', value: formatInr(outstandingAmount), sub: `${outstandingCount} invoice${outstandingCount !== 1 ? 's' : ''} pending`, accent: 'linear-gradient(90deg, #f59e0b, #fcd34d)' },
          { label: 'Draft', value: formatInr(draftAmount), sub: `${draftCount} draft${draftCount !== 1 ? 's' : ''}`, accent: 'linear-gradient(90deg, #7C85C0, #D6DAF0)' },
        ].map((card) => (
          <div
            key={card.label}
            style={{
              flex: 1, background: '#fff', border: '1px solid #E8EAF6', borderRadius: 12,
              padding: '16px 20px', position: 'relative', overflow: 'hidden',
              boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: card.accent }} />
            <div style={{ fontSize: 12, fontWeight: 600, color: '#7C85C0', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {card.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#1e1b4b', marginTop: 4 }}>{card.value}</div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {/* Action Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '6px 12px', fontSize: 13, border: '1px solid #D6DAF0', borderRadius: 8,
              color: '#1e1b4b', background: '#fff', cursor: 'pointer',
            }}
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="APPROVED">Approved</option>
            <option value="PAID">Paid</option>
          </select>
          <span style={{ fontSize: 14, color: '#6b7280' }}>
            {invoices.length} invoice{invoices.length !== 1 ? 's' : ''}
          </span>
        </div>
        {canManage && (
          <button
            onClick={openAdd}
            style={{
              background: 'linear-gradient(135deg, #FF4B2B, #E63E1F)',
              color: '#fff', border: 'none', padding: '8px 18px', borderRadius: 8,
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 6,
              boxShadow: '0 2px 6px rgba(255,75,43,0.3)',
            }}
          >
            <Plus size={14} /> Create Invoice
          </button>
        )}
      </div>

      {invoices.length === 0 ? (
        <div
          style={{
            background: '#fff', borderRadius: 12,
            boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            border: '1px solid #E8EAF6', textAlign: 'center', padding: '60px 20px', color: '#7C85C0',
          }}
        >
          No invoices match this filter.
        </div>
      ) : (
        <div
          style={{
            background: '#fff', borderRadius: 12,
            boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            border: '1px solid #E8EAF6', overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'linear-gradient(135deg, rgba(43,57,144,0.03), rgba(74,91,181,0.02))' }}>
                {['Invoice Date', projectType === 'FIXED_PRICE' ? 'Milestone' : 'Billing Period', 'Amount', 'Exch. Rate', 'Amount (INR)', 'Status', 'Notes', 'Actions'].map((h, i) => (
                  <th
                    key={h}
                    style={{
                      padding: '12px 16px',
                      textAlign: i === 2 || i === 3 || i === 4 ? 'right' : i === 5 || i === 7 ? 'center' : 'left',
                      fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5,
                      color: '#7C85C0', borderBottom: '1px solid #E8EAF6',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => {
                const badgeStyle = STATUS_BADGE_STYLES[inv.status] ?? STATUS_BADGE_STYLES.DRAFT
                const forwardBtn = FORWARD_BUTTON_CONFIG[inv.status]
                const canEditRow = inv.status === 'DRAFT' && canManage
                const canTransitionRow = canManage && !!forwardBtn

                return (
                  <tr
                    key={inv.id}
                    style={{
                      borderBottom: '1px solid #E8EAF6',
                      cursor: canEditRow ? 'pointer' : 'default',
                    }}
                    onClick={() => openEdit(inv)}
                  >
                    <td style={{ padding: '12px 16px', fontSize: 14 }}>
                      {inv.invoice_date ? formatDate(inv.invoice_date) : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14 }}>
                      {projectType === 'FIXED_PRICE'
                        ? inv.milestone?.name ?? '—'
                        : inv.billing_period_start && inv.billing_period_end
                          ? `${formatDate(inv.billing_period_start)} – ${formatDate(inv.billing_period_end)}`
                          : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right' }}>
                      {inv.amount != null ? formatMoney(inv.amount, inv.currency) : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right' }}>
                      {inv.exchange_rate ?? '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right' }}>
                      {inv.amount_inr != null ? <strong>{formatInr(inv.amount_inr)}</strong> : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                          borderRadius: 20, fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                          letterSpacing: 0.5, background: badgeStyle.bg, color: badgeStyle.color,
                        }}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: '12px 16px', fontSize: 13, color: '#6b7280', maxWidth: 150,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}
                    >
                      {inv.notes || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                      {canEditRow || canTransitionRow ? (
                        <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                          {canEditRow && renderActionBtn('edit', 'Edit', () => openEdit(inv))}
                          {canTransitionRow && renderActionBtn(forwardBtn.className, forwardBtn.label, () => handleTransition(inv))}
                        </div>
                      ) : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <InvoiceFormModal
        open={modalOpen}
        projectId={projectId}
        projectType={projectType}
        billingCurrency={billingCurrency}
        editingInvoice={editingInvoice}
        onClose={() => { setModalOpen(false); setEditingInvoice(null) }}
      />

      <ConfirmDialog
        open={!!confirmTransition}
        title={`${confirmTransition?.label}`}
        description={`Are you sure you want to ${confirmTransition?.label.toLowerCase()} this invoice? This will transition the status to ${confirmTransition?.targetStatus}.`}
        confirmLabel={confirmTransition?.label ?? 'Confirm'}
        variant="default"
        onConfirm={() =>
          confirmTransition &&
          transitionMut.mutate({
            invoiceId: confirmTransition.invoice.id,
            status: confirmTransition.targetStatus,
          })
        }
        onCancel={() => setConfirmTransition(null)}
      />
    </div>
  )
}
