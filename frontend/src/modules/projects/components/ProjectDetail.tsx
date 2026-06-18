import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams, useSearchParams, Link } from 'react-router'
import { toast } from 'sonner'
import { Pencil, Calendar, User, Coins } from 'lucide-react'
import { useAuthStore } from '../../auth/store'
import { fetchProject, transitionProjectStatus } from '../api'
import { StatusBadge, TypeBadge, Breadcrumb, ConfirmDialog } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'
import { AssignmentList } from '../../allocations/components/AssignmentList'
import { AssignmentFormModal } from '../../allocations/components/AssignmentFormModal'
import { WorklogTab } from '../../worklogs/components/WorklogTab'
import { NonHumanCostTab } from '../../nonhuman_costs/components/NonHumanCostTab'
import { MilestoneTab } from '../../invoicing/components/MilestoneTab'
import { InvoiceTab } from '../../invoicing/components/InvoiceTab'
import type { AssignmentListItem } from '../../allocations/api'

// See FSD §10 — valid status transitions
const TRANSITIONS: Record<string, { label: string; target: string; variant: 'default' | 'danger' }[]> = {
  ACTIVE: [
    { label: 'Complete', target: 'COMPLETED', variant: 'default' },
    { label: 'Put on Hold', target: 'ON_HOLD', variant: 'default' },
    { label: 'Cancel', target: 'CANCELLED', variant: 'danger' },
  ],
  ON_HOLD: [
    { label: 'Resume', target: 'ACTIVE', variant: 'default' },
    { label: 'Cancel', target: 'CANCELLED', variant: 'danger' },
  ],
}

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canEdit = user && ['CEO', 'CTO', 'DM', 'PM'].includes(user.role.code)
  const canTransition = user && ['CEO', 'CTO', 'DM'].includes(user.role.code)
  const canViewCosts = user && ['CEO', 'CTO', 'DM', 'PM', 'FINANCE'].includes(user.role.code)
  const canViewMilestones = user && ['CEO', 'CTO', 'DM', 'PM', 'FINANCE'].includes(user.role.code)
  const canViewInvoices = user && ['CEO', 'CTO', 'FINANCE'].includes(user.role.code)

  type TabKey = 'assignments' | 'milestones' | 'invoices' | 'worklogs' | 'costs'
  const requestedTab = searchParams.get('tab') as TabKey | null
  const [activeTab, setActiveTab] = useState<TabKey>(
    requestedTab && ['assignments', 'milestones', 'invoices', 'worklogs', 'costs'].includes(requestedTab)
      ? requestedTab
      : 'assignments',
  )
  const [confirmTransition, setConfirmTransition] = useState<{ target: string; label: string; variant: 'default' | 'danger' } | null>(null)
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false)
  const [editingAssignment, setEditingAssignment] = useState<AssignmentListItem | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => fetchProject(id!),
    enabled: !!id,
  })

  const transitionMut = useMutation({
    mutationFn: (status: string) => transitionProjectStatus(id!, status),
    onSuccess: () => {
      toast.success('Project status updated')
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setConfirmTransition(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || 'Failed to update status')
      setConfirmTransition(null)
    },
  })

  const p = data?.data
  useDocumentTitle(p?.name)

  if (isLoading) return <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
  if (!p) return <div className="py-8 text-center text-[14px]" style={{ color: '#ef4444' }}>Project not found</div>

  const availableTransitions = TRANSITIONS[p.status] ?? []
  const tabs = [
    { key: 'assignments' as const, label: 'Assignments' },
    ...(p.type === 'FIXED_PRICE' && canViewMilestones ? [{ key: 'milestones' as const, label: 'Milestones' }] : []),
    ...(canViewInvoices ? [{ key: 'invoices' as const, label: 'Invoices' }] : []),
    ...(p.worklog_enabled ? [{ key: 'worklogs' as const, label: 'Worklogs' }] : []),
    ...(canViewCosts ? [{ key: 'costs' as const, label: 'Non-Human Costs' }] : []),
  ]

  return (
    <div>
      <Breadcrumb items={[{ label: 'Projects', to: '/projects' }, { label: p.name }]} />

      {/* Header Card */}
      <div className="mb-5 rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>{p.name}</h1>
              <TypeBadge type={p.type} />
              <StatusBadge status={p.status} />
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-[13.5px]" style={{ color: '#6b7280' }}>
              <span>
                Client:{' '}
                <Link to={`/clients/${p.client.id}`} className="font-medium no-underline" style={{ color: '#2B3990' }}>
                  {p.client.name}
                </Link>
              </span>
              <span className="flex items-center gap-1">
                <Coins size={14} /> {p.billing_currency}
              </span>
              <span className="flex items-center gap-1">
                <User size={14} /> DM: {p.dm.name}
              </span>
              <span className="flex items-center gap-1">
                <User size={14} /> PM: {p.pm.name}
              </span>
              {p.start_date && (
                <span className="flex items-center gap-1">
                  <Calendar size={14} /> {p.start_date}
                </span>
              )}
              {p.contract_end_date && (
                <span className="flex items-center gap-1">
                  <Calendar size={14} /> End: {p.contract_end_date}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {canTransition && availableTransitions.map((t) => (
              <button
                key={t.target}
                onClick={() => setConfirmTransition(t)}
                className="rounded-lg px-4 py-2 text-[13px] font-medium transition-colors"
                style={{
                  border: `1px solid ${t.variant === 'danger' ? '#fecaca' : '#D6DAF0'}`,
                  background: '#fff',
                  color: t.variant === 'danger' ? '#dc2626' : '#2B3990',
                }}
              >
                {t.label}
              </button>
            ))}
            {canEdit && (
              <button
                onClick={() => navigate(`/projects/${id}/edit`)}
                className="flex items-center gap-1.5 rounded-lg border-none px-4 py-2 text-[13px] font-semibold text-white transition-all"
                style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)', boxShadow: '0 2px 8px rgba(43,57,144,0.25)' }}
              >
                <Pencil size={14} />
                Edit
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1" style={{ borderBottom: '2px solid #E8EAF6' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="border-none px-5 py-2.5 text-[14px] font-medium transition-colors"
            style={{
              background: 'transparent',
              color: activeTab === tab.key ? '#2B3990' : '#6b7280',
              borderBottom: activeTab === tab.key ? '2px solid #FF4B2B' : '2px solid transparent',
              marginBottom: '-2px',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'assignments' && (
        <AssignmentList
          projectId={id!}
          onAddAssignment={() => { setEditingAssignment(null); setAssignmentModalOpen(true) }}
          onEditAssignment={(a) => { setEditingAssignment(a); setAssignmentModalOpen(true) }}
        />
      )}
      {activeTab === 'milestones' && (
        <MilestoneTab projectId={id!} billingCurrency={p.billing_currency} />
      )}
      {activeTab === 'invoices' && (
        <InvoiceTab projectId={id!} projectType={p.type} billingCurrency={p.billing_currency} />
      )}
      {activeTab === 'worklogs' && <WorklogTab projectId={id!} />}
      {activeTab === 'costs' && (
        <NonHumanCostTab
          projectId={id!}
          canEdit={!!canEdit}
        />
      )}

      <ConfirmDialog
        open={!!confirmTransition}
        title={`${confirmTransition?.label} Project`}
        description={`Are you sure you want to ${confirmTransition?.label.toLowerCase()} "${p.name}"? This will change the project status.`}
        confirmLabel={confirmTransition?.label ?? 'Confirm'}
        variant={confirmTransition?.variant ?? 'default'}
        onConfirm={() => confirmTransition && transitionMut.mutate(confirmTransition.target)}
        onCancel={() => setConfirmTransition(null)}
      />

      <AssignmentFormModal
        open={assignmentModalOpen}
        projectId={id!}
        projectName={p.name}
        projectCurrency={p.billing_currency}
        editingAssignment={editingAssignment}
        onClose={() => { setAssignmentModalOpen(false); setEditingAssignment(null) }}
      />
    </div>
  )
}
