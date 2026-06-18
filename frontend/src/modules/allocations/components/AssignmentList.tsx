import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { AlertTriangle, Users } from 'lucide-react'
import { useAuthStore } from '../../auth/store'
import { fetchProjectAssignments, releaseAssignment } from '../api'
import type { AssignmentListItem } from '../api'
import { StatusBadge, ConfirmDialog, SearchableSelect } from '../../../shared/components'
import { format, parseISO } from 'date-fns'

interface AssignmentListProps {
  projectId: string
  onAddAssignment?: () => void
  onEditAssignment?: (assignment: AssignmentListItem) => void
}

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'RELEASED', label: 'Released' },
  { value: 'AUTO_RELEASED', label: 'Auto-Released' },
]

const CURRENCY_SYMBOLS: Record<string, string> = { INR: '₹', USD: '$', EUR: '€', GBP: '£' }
function currencySymbol(code: string): string { return CURRENCY_SYMBOLS[code] ?? code }

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Ongoing'
  return format(parseISO(dateStr), 'dd MMM yyyy')
}

export function AssignmentList({ projectId, onAddAssignment, onEditAssignment }: AssignmentListProps) {
  const { user } = useAuthStore()
  const roleCode = user?.role.code ?? ''
  const canEdit = ['CEO', 'CTO', 'DM', 'PM'].includes(roleCode)
  const canSeeBillability = !['HR', 'ENGINEER'].includes(roleCode)
  const canSeeShadow = !['HR', 'ENGINEER'].includes(roleCode)
  const canSeeRate = ['CEO', 'CTO', 'FINANCE', 'DM'].includes(roleCode)

  const [statusFilter, setStatusFilter] = useState('ACTIVE')
  const [releaseTarget, setReleaseTarget] = useState<AssignmentListItem | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['project-assignments', projectId, statusFilter],
    queryFn: () => fetchProjectAssignments(projectId, statusFilter || undefined),
  })

  const releaseMut = useMutation({
    mutationFn: (id: string) => releaseAssignment(id),
    onSuccess: () => {
      toast.success('Assignment released')
      queryClient.invalidateQueries({ queryKey: ['project-assignments', projectId] })
      setReleaseTarget(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || 'Failed to release assignment')
      setReleaseTarget(null)
    },
  })

  const assignments = data?.data ?? []

  // See FSD §6.1 — over-allocation: any resource with total > 100% across all active assignments
  const overAllocated = assignments.filter(
    (a) => a.status === 'ACTIVE' && a.allocation_pct > 100,
  )
  // We can only detect per-row allocation > 100 from this endpoint.
  // The real over-allocation check happens across projects, but we show the banner
  // if any assignment's allocation_pct alone exceeds 100.
  // The backend also returns warnings on create/update for cross-project over-allocation.

  if (isLoading) {
    return (
      <div className="flex items-center justify-center rounded-xl py-16" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="text-[13.5px]" style={{ color: '#7C85C0' }}>Loading assignments...</div>
      </div>
    )
  }

  return (
    <div>
      {/* Over-allocation Banner */}
      {overAllocated.length > 0 && (
        <div
          className="mb-4 flex items-center gap-2.5 rounded-xl px-5 py-3 text-[13px] font-medium"
          style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }}
        >
          <AlertTriangle size={18} />
          <span>
            <strong>Over-Allocation Detected:</strong>{' '}
            {overAllocated.map((a) => a.resource?.name).filter(Boolean).join(', ')}{' '}
            {overAllocated.length === 1 ? 'is' : 'are'} allocated over 100%.
          </span>
        </div>
      )}

      {/* Header & Filter */}
      <div className="mb-4 flex items-center justify-between">
        <div className="text-[16px] font-bold" style={{ color: '#1e1b4b' }}>
          Project Assignments ({assignments.length})
        </div>
        {canEdit && (
          <button
            onClick={onAddAssignment}
            className="flex items-center gap-1.5 rounded-lg border-none px-5 py-2 text-[13px] font-semibold text-white transition-all"
            style={{ background: '#FF4B2B', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}
          >
            + Add Assignment
          </button>
        )}
      </div>

      <div className="mb-4">
        <SearchableSelect
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_OPTIONS}
          placeholder="All Statuses"
          variant="filter"
        />
      </div>

      {/* Table or Empty State */}
      {assignments.length === 0 ? (
        <div
          className="flex items-center justify-center rounded-xl py-16 text-center"
          style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
        >
          <div>
            <Users size={48} className="mx-auto mb-4 opacity-40" style={{ color: '#7C85C0' }} />
            <p className="mb-1 text-[16px] font-semibold" style={{ color: '#1e1b4b' }}>No assignments yet</p>
            <p className="mb-4 text-[13px]" style={{ color: '#6b7280' }}>Add a resource to this project.</p>
            {canEdit && (
              <button
                onClick={onAddAssignment}
                className="rounded-lg border-none px-5 py-2 text-[13px] font-semibold text-white"
                style={{ background: '#FF4B2B' }}
              >
                + Add Assignment
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}>
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Resource</th>
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Eff. Designation</th>
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Allocation %</th>
                {canSeeBillability && (
                  <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Billability %</th>
                )}
                {canSeeShadow && (
                  <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Shadow</th>
                )}
                {canSeeRate && (
                  <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Billing Rate</th>
                )}
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Start Date</th>
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>End Date</th>
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Status</th>
                {canEdit && (
                  <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {assignments.map((a, idx) => (
                <tr
                  key={a.id}
                  className="cursor-pointer transition-colors"
                  style={{
                    borderBottom: '1px solid #E8EAF6',
                    background: idx % 2 === 0 ? '#fff' : '#F5F6FC',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#E8EAF6' }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#F5F6FC' }}
                  onClick={() => onEditAssignment?.(a)}
                >
                  <td className="px-3.5 py-3 text-[13px]">
                    {a.resource ? (
                      <Link
                        to={`/resources/${a.resource.id}`}
                        className="font-semibold no-underline"
                        style={{ color: '#2B3990' }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {a.resource.name}
                      </Link>
                    ) : (
                      <span style={{ color: '#6b7280' }}>—</span>
                    )}
                  </td>
                  <td className="px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                    {a.effective_designation || '—'}
                  </td>
                  <td className="px-3.5 py-3 text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                    {a.allocation_pct}%
                  </td>
                  {canSeeBillability && (
                    <td className="px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                      {a.billability_pct !== null ? `${a.billability_pct}%` : '—'}
                    </td>
                  )}
                  {canSeeShadow && (
                    <td className="px-3.5 py-3 text-[13px]">
                      {a.is_shadow ? (
                        <span
                          className="inline-block rounded-xl px-2.5 py-0.5 text-[11px] font-semibold"
                          style={{ background: '#ede9fe', color: '#6d28d9' }}
                        >
                          Shadow
                        </span>
                      ) : (
                        <span style={{ color: '#7C85C0' }}>—</span>
                      )}
                    </td>
                  )}
                  {canSeeRate && (
                    <td className="px-3.5 py-3 text-[13px] font-medium" style={{ color: '#1e1b4b' }}>
                      {a.billing_rate != null ? `${currencySymbol(a.billing_currency)}${a.billing_rate.toLocaleString('en-IN')}` : '—'}
                    </td>
                  )}
                  <td className="whitespace-nowrap px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                    {formatDate(a.start_date)}
                  </td>
                  <td className="whitespace-nowrap px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                    {formatDate(a.end_date)}
                  </td>
                  <td className="px-3.5 py-3 text-[13px]">
                    <StatusBadge status={a.status} />
                  </td>
                  {canEdit && (
                    <td className="px-3.5 py-3 text-[13px]" onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => onEditAssignment?.(a)}
                          className="rounded-md px-3 py-1 text-[12px] font-medium text-white"
                          style={{ background: '#2B3990', border: 'none' }}
                        >
                          Edit
                        </button>
                        {a.status === 'ACTIVE' && (
                          <button
                            onClick={() => setReleaseTarget(a)}
                            className="rounded-md px-3 py-1 text-[12px] font-medium"
                            style={{ background: '#fef2f2', color: '#ef4444', border: '1px solid #fecaca' }}
                          >
                            Release
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={!!releaseTarget}
        title="Confirm Release"
        description={`Are you sure you want to release ${releaseTarget?.resource?.name ?? 'this resource'} from this project? This action cannot be undone.`}
        confirmLabel="Release"
        variant="danger"
        onConfirm={() => releaseTarget && releaseMut.mutate(releaseTarget.id)}
        onCancel={() => setReleaseTarget(null)}
      />
    </div>
  )
}
