// See FSD §6.2 — Milestone lifecycle and transition UI
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Plus, GripVertical } from 'lucide-react'
import { fetchMilestones, transitionMilestoneStatus, type Milestone, type MilestoneStatus } from '../api'
import { MilestoneFormModal } from './MilestoneFormModal'
import { ConfirmDialog } from '../../../shared/components'
import { useAuthStore } from '../../auth/store'

// See FSD §6.2 — Milestone status transitions
const FORWARD_TRANSITIONS: Record<string, MilestoneStatus> = {
  PLANNED: 'DELIVERED',
  DELIVERED: 'APPROVED',
  APPROVED: 'INVOICED',
  INVOICED: 'PAID',
}

const BACKWARD_TRANSITIONS: Record<string, MilestoneStatus> = {
  DELIVERED: 'PLANNED',
  APPROVED: 'DELIVERED',
}

const FINANCE_ONLY_TRANSITIONS = new Set(['APPROVED→INVOICED', 'INVOICED→PAID'])

const FORWARD_BUTTON_CONFIG: Record<string, { label: string; className: string }> = {
  PLANNED: { label: 'Mark Delivered', className: 'deliver' },
  DELIVERED: { label: 'Approve', className: 'approve' },
  APPROVED: { label: 'Create Invoice', className: 'invoice' },
  INVOICED: { label: 'Mark Paid', className: 'paid' },
}

const BACKWARD_BUTTON_CONFIG: Record<string, { label: string; className: string }> = {
  DELIVERED: { label: 'Reject', className: 'reject' },
  APPROVED: { label: 'Withdraw Approval', className: 'reject' },
}

// See SCREENS.md — milestone status badge colors from mockup
const STATUS_BADGE_STYLES: Record<string, { bg: string; color: string }> = {
  PLANNED: { bg: '#e0e7ff', color: '#3730a3' },
  DELIVERED: { bg: '#dbeafe', color: '#1e40af' },
  APPROVED: { bg: '#dcfce7', color: '#166534' },
  INVOICED: { bg: '#fef3c7', color: '#92400e' },
  PAID: { bg: '#d1fae5', color: '#065f46' },
}

const ACTION_BTN_STYLES: Record<string, { bg: string; color: string; border: string; hoverBg: string }> = {
  deliver: { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe', hoverBg: '#dbeafe' },
  approve: { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', hoverBg: '#dcfce7' },
  invoice: { bg: '#FFF0EC', color: '#FF4B2B', border: '#fecaca', hoverBg: '#ffe4e0' },
  paid: { bg: '#ecfdf5', color: '#047857', border: '#a7f3d0', hoverBg: '#d1fae5' },
  reject: { bg: '#fef2f2', color: '#b91c1c', border: '#fecaca', hoverBg: '#fee2e2' },
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatInr(val: number): string {
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function getDelayDays(planned: string, actual: string): number | null {
  const p = new Date(planned + 'T00:00:00')
  const a = new Date(actual + 'T00:00:00')
  const diff = Math.floor((a.getTime() - p.getTime()) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : null
}

interface MilestoneTabProps {
  projectId: string
  billingCurrency: string
}

export function MilestoneTab({ projectId, billingCurrency }: MilestoneTabProps) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const roleCode = user?.role.code ?? ''

  const canManage = ['CEO', 'CTO', 'DM', 'PM'].includes(roleCode)
  const canFinanceTransition = ['CEO', 'CTO', 'FINANCE'].includes(roleCode)

  const [modalOpen, setModalOpen] = useState(false)
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null)
  const [confirmTransition, setConfirmTransition] = useState<{
    milestone: Milestone
    targetStatus: MilestoneStatus
    label: string
    isBackward: boolean
  } | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['project-milestones', projectId],
    queryFn: () => fetchMilestones(projectId),
  })

  const transitionMut = useMutation({
    mutationFn: ({ milestoneId, status }: { milestoneId: string; status: MilestoneStatus }) =>
      transitionMilestoneStatus(projectId, milestoneId, status),
    onSuccess: () => {
      toast.success('Milestone status updated')
      queryClient.invalidateQueries({ queryKey: ['project-milestones', projectId] })
      setConfirmTransition(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || 'Failed to update milestone status')
      setConfirmTransition(null)
    },
  })

  const milestones: Milestone[] = data?.data ?? []

  // See SCREENS.md — Summary cards
  const totalAmount = milestones.reduce((s, m) => s + (m.amount ?? 0), 0)
  const deliveredStatuses = ['DELIVERED', 'APPROVED', 'INVOICED', 'PAID']
  const deliveredAmount = milestones.filter((m) => deliveredStatuses.includes(m.status)).reduce((s, m) => s + (m.amount ?? 0), 0)
  const deliveredCount = milestones.filter((m) => deliveredStatuses.includes(m.status)).length
  const invoicedStatuses = ['INVOICED', 'PAID']
  const invoicedAmount = milestones.filter((m) => invoicedStatuses.includes(m.status)).reduce((s, m) => s + (m.amount ?? 0), 0)
  const invoicedCount = milestones.filter((m) => invoicedStatuses.includes(m.status)).length
  const remainingAmount = milestones.filter((m) => m.status === 'PLANNED').reduce((s, m) => s + (m.amount ?? 0), 0)
  const remainingCount = milestones.filter((m) => m.status === 'PLANNED').length

  function canDoForwardTransition(m: Milestone): boolean {
    const forward = FORWARD_TRANSITIONS[m.status]
    if (!forward) return false
    const key = `${m.status}→${forward}`
    if (FINANCE_ONLY_TRANSITIONS.has(key)) return canFinanceTransition
    return canManage
  }

  function canDoBackwardTransition(m: Milestone): boolean {
    if (!BACKWARD_TRANSITIONS[m.status]) return false
    return canManage
  }

  function handleForward(m: Milestone) {
    const target = FORWARD_TRANSITIONS[m.status]
    if (!target) return
    const btn = FORWARD_BUTTON_CONFIG[m.status]
    setConfirmTransition({ milestone: m, targetStatus: target, label: btn.label, isBackward: false })
  }

  function handleBackward(m: Milestone) {
    const target = BACKWARD_TRANSITIONS[m.status]
    if (!target) return
    const btn = BACKWARD_BUTTON_CONFIG[m.status]
    setConfirmTransition({ milestone: m, targetStatus: target, label: btn.label, isBackward: true })
  }

  function openAdd() {
    setEditingMilestone(null)
    setModalOpen(true)
  }

  function openEdit(m: Milestone) {
    if (m.status !== 'PLANNED' || !canManage) return
    setEditingMilestone(m)
    setModalOpen(true)
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
    return <div style={{ padding: 40, textAlign: 'center', color: '#7C85C0', fontSize: 14 }}>Loading milestones...</div>
  }

  // Empty state
  if (milestones.length === 0) {
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
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b', marginBottom: 8 }}>No milestones yet</div>
            <div style={{ fontSize: 14, color: '#7C85C0', maxWidth: 400, margin: '0 auto' }}>
              Add milestones to track deliverables and link them to invoices for revenue recognition.
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
                <Plus size={14} /> Add Milestone
              </button>
            )}
          </div>
        </div>
        <MilestoneFormModal
          open={modalOpen}
          projectId={projectId}
          editingMilestone={editingMilestone}
          onClose={() => { setModalOpen(false); setEditingMilestone(null) }}
        />
      </>
    )
  }

  return (
    <div>
      {/* Summary Cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        {[
          { label: 'Contract Value', value: formatInr(totalAmount), sub: `${milestones.length} milestones` },
          { label: 'Delivered', value: formatInr(deliveredAmount), sub: `${deliveredCount} milestones` },
          { label: 'Invoiced / Paid', value: formatInr(invoicedAmount), sub: `${invoicedCount} milestones` },
          { label: 'Remaining', value: formatInr(remainingAmount), sub: `${remainingCount} milestones planned` },
        ].map((card) => (
          <div
            key={card.label}
            style={{
              flex: 1, background: '#fff', border: '1px solid #E8EAF6', borderRadius: 12,
              padding: '16px 20px',
              boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            }}
          >
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
        <span style={{ fontSize: 14, color: '#6b7280' }}>
          Showing {milestones.length} milestone{milestones.length !== 1 ? 's' : ''}
        </span>
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
            <Plus size={14} /> Add Milestone
          </button>
        )}
      </div>

      {/* Table */}
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
              {['#', 'Milestone Name', 'Amount', 'Planned Date', 'Actual Date', 'Status', 'Delay', 'Actions'].map((h, i) => (
                <th
                  key={h}
                  style={{
                    padding: '12px 16px',
                    textAlign: i === 2 ? 'right' : i === 5 || i === 7 ? 'center' : 'left',
                    fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5,
                    color: '#7C85C0', borderBottom: '1px solid #E8EAF6',
                    ...(i === 0 ? { width: 40 } : {}),
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {milestones.map((m) => {
              const delayDays =
                m.actual_delivery_date && m.planned_delivery_date
                  ? getDelayDays(m.planned_delivery_date, m.actual_delivery_date)
                  : null
              const isDelayed = delayDays !== null && delayDays > 0
              const badgeStyle = STATUS_BADGE_STYLES[m.status] ?? STATUS_BADGE_STYLES.PLANNED
              const forwardBtn = FORWARD_BUTTON_CONFIG[m.status]
              const backwardBtn = BACKWARD_BUTTON_CONFIG[m.status]

              return (
                <tr
                  key={m.id}
                  style={{
                    background: isDelayed ? '#fef3c7' : '#fff',
                    borderBottom: '1px solid #E8EAF6',
                    cursor: m.status === 'PLANNED' && canManage ? 'pointer' : 'default',
                  }}
                  onClick={() => openEdit(m)}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <GripVertical size={16} style={{ color: '#7C85C0', cursor: 'grab' }} />
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 14 }}>
                    <strong>{m.name}</strong>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right' }}>
                    {m.amount != null ? formatInr(m.amount) : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 14 }}>
                    {m.planned_delivery_date ? formatDate(m.planned_delivery_date) : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 14 }}>
                    {m.actual_delivery_date ? formatDate(m.actual_delivery_date) : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    <span
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                        borderRadius: 20, fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                        letterSpacing: 0.5, background: badgeStyle.bg, color: badgeStyle.color,
                      }}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12 }}>
                    {isDelayed ? (
                      <span style={{ color: '#f59e0b', fontWeight: 600 }}>Delayed {delayDays} days</span>
                    ) : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    {(canDoForwardTransition(m) || canDoBackwardTransition(m)) ? (
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                        {canDoForwardTransition(m) && forwardBtn &&
                          renderActionBtn(forwardBtn.className, forwardBtn.label, () => handleForward(m))}
                        {canDoBackwardTransition(m) && backwardBtn &&
                          renderActionBtn(backwardBtn.className, backwardBtn.label, () => handleBackward(m))}
                      </div>
                    ) : '—'}
                  </td>
                </tr>
              )
            })}
            {/* Total Row */}
            <tr style={{ fontWeight: 700, background: '#F5F6FC' }}>
              <td style={{ padding: '12px 16px' }} />
              <td style={{ padding: '12px 16px', fontSize: 14 }}><strong>Total Contract Value</strong></td>
              <td style={{ padding: '12px 16px', fontSize: 14, textAlign: 'right' }}><strong>{formatInr(totalAmount)}</strong></td>
              <td colSpan={5} style={{ padding: '12px 16px' }} />
            </tr>
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: '#6b7280', padding: '8px 0' }}>
        {[
          { status: 'PLANNED', desc: 'Deliverable scheduled' },
          { status: 'DELIVERED', desc: 'Work completed, pending approval' },
          { status: 'APPROVED', desc: 'Ready for invoicing' },
          { status: 'INVOICED', desc: 'Invoice raised, awaiting payment' },
          { status: 'PAID', desc: 'Payment received' },
        ].map(({ status, desc }) => {
          const s = STATUS_BADGE_STYLES[status]
          return (
            <span key={status}>
              <span
                style={{
                  display: 'inline-flex', alignItems: 'center', padding: '2px 8px',
                  borderRadius: 12, fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
                  background: s.bg, color: s.color, marginRight: 4,
                }}
              >
                {status}
              </span>
              {desc}
            </span>
          )
        })}
      </div>

      <MilestoneFormModal
        open={modalOpen}
        projectId={projectId}
        editingMilestone={editingMilestone}
        onClose={() => { setModalOpen(false); setEditingMilestone(null) }}
      />

      <ConfirmDialog
        open={!!confirmTransition}
        title={`${confirmTransition?.label}`}
        description={
          confirmTransition?.isBackward
            ? `Are you sure you want to ${confirmTransition.label.toLowerCase()} "${confirmTransition.milestone.name}"? This will revert the status to ${confirmTransition.targetStatus}.`
            : `Are you sure you want to transition "${confirmTransition?.milestone.name}" to ${confirmTransition?.targetStatus}?`
        }
        confirmLabel={confirmTransition?.label ?? 'Confirm'}
        variant={confirmTransition?.isBackward ? 'danger' : 'default'}
        onConfirm={() =>
          confirmTransition &&
          transitionMut.mutate({
            milestoneId: confirmTransition.milestone.id,
            status: confirmTransition.targetStatus,
          })
        }
        onCancel={() => setConfirmTransition(null)}
      />
    </div>
  )
}
