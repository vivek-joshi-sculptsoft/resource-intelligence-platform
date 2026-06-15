import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { Info, ChevronDown, ChevronUp, Briefcase } from 'lucide-react'
import { useAuthStore } from '../../auth/store'
import { fetchResourceAssignments } from '../api'
import type { AssignmentListItem } from '../api'
import { StatusBadge } from '../../../shared/components'
import { format, parseISO } from 'date-fns'

interface ResourceAssignmentsPanelProps {
  resourceId: string
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Ongoing'
  return format(parseISO(dateStr), 'dd MMM yyyy')
}

export function ResourceAssignmentsPanel({ resourceId }: ResourceAssignmentsPanelProps) {
  const { user } = useAuthStore()
  const roleCode = user?.role.code ?? ''
  const canSeeBillability = !['HR', 'ENGINEER'].includes(roleCode)
  const canSeeShadow = !['HR', 'ENGINEER'].includes(roleCode)

  const [showHistory, setShowHistory] = useState(false)

  const { data: activeData, isLoading: activeLoading } = useQuery({
    queryKey: ['resource-assignments', resourceId, 'ACTIVE'],
    queryFn: () => fetchResourceAssignments(resourceId, 'ACTIVE'),
  })

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['resource-assignments-history', resourceId],
    queryFn: () => fetchResourceAssignments(resourceId),
    enabled: showHistory,
  })

  const activeAssignments = activeData?.data ?? []
  const allAssignments = historyData?.data ?? []
  const releasedAssignments = allAssignments.filter((a) => a.status === 'RELEASED' || a.status === 'AUTO_RELEASED')
  const totalAlloc = activeAssignments.reduce((s, a) => s + a.allocation_pct, 0)

  function renderTable(assignments: AssignmentListItem[], showReleasedAt: boolean) {
    return (
      <div className="overflow-hidden rounded-xl" style={{ border: '1px solid #E8EAF6' }}>
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Project</th>
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Eff. Designation</th>
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Allocation %</th>
              {canSeeBillability && (
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Billability %</th>
              )}
              {canSeeShadow && !showReleasedAt && (
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Shadow</th>
              )}
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Start Date</th>
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>End Date</th>
              <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Status</th>
              {showReleasedAt && (
                <th className="px-3.5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-white" style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)' }}>Released On</th>
              )}
            </tr>
          </thead>
          <tbody>
            {assignments.map((a, idx) => (
              <tr
                key={a.id}
                style={{
                  borderBottom: '1px solid #E8EAF6',
                  background: idx % 2 === 0 ? '#fff' : '#F5F6FC',
                }}
              >
                <td className="px-3.5 py-3 text-[13px]">
                  {a.project_id ? (
                    <Link
                      to={`/projects/${a.project_id}`}
                      className="font-semibold no-underline"
                      style={{ color: '#2B3990' }}
                    >
                      {(a as any).project?.name ?? 'View Project'}
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
                {canSeeShadow && !showReleasedAt && (
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
                <td className="whitespace-nowrap px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                  {formatDate(a.start_date)}
                </td>
                <td className="whitespace-nowrap px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                  {formatDate(a.end_date)}
                </td>
                <td className="px-3.5 py-3 text-[13px]">
                  <StatusBadge status={a.status} />
                </td>
                {showReleasedAt && (
                  <td className="whitespace-nowrap px-3.5 py-3 text-[13px]" style={{ color: '#1e1b4b' }}>
                    {a.released_at ? formatDate(a.released_at.split('T')[0]) : '—'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {/* Allocation total footer for active */}
        {!showReleasedAt && assignments.length > 0 && (
          <div
            className="flex items-center justify-between px-4 py-3"
            style={{ borderTop: '2px solid #D6DAF0', background: '#F5F6FC' }}
          >
            <span className="text-[13px] font-bold" style={{ color: '#1e1b4b' }}>Total Allocation</span>
            <span
              className="text-[16px] font-extrabold"
              style={{ color: totalAlloc > 100 ? '#ef4444' : '#2B3990' }}
            >
              {totalAlloc}%
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      {/* Read-only note */}
      <div
        className="mb-4 flex items-center gap-2 rounded-lg px-4 py-2.5 text-[13px]"
        style={{ background: '#F0F1FA', border: '1px solid #E8EAF6', color: '#6b7280' }}
      >
        <Info size={15} style={{ color: '#7C85C0' }} />
        This is a read-only view. Assignment edits are made from the project detail page.
      </div>

      {/* Active Assignments */}
      <div
        className="mb-4 rounded-xl p-6"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        <div className="mb-4">
          <h2 className="text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Active Assignments</h2>
          {activeAssignments.length > 0 && (
            <p className="text-[13px]" style={{ color: '#6b7280' }}>
              Currently allocated across {activeAssignments.length} project{activeAssignments.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {activeLoading ? (
          <div className="py-8 text-center text-[13px]" style={{ color: '#7C85C0' }}>Loading...</div>
        ) : activeAssignments.length === 0 ? (
          <div className="py-8 text-center">
            <Briefcase size={48} className="mx-auto mb-4 opacity-40" style={{ color: '#7C85C0' }} />
            <p className="mb-1 text-[16px] font-semibold" style={{ color: '#1e1b4b' }}>No active assignments</p>
            <p className="text-[13px]" style={{ color: '#6b7280' }}>This resource is currently on bench.</p>
          </div>
        ) : (
          renderTable(activeAssignments, false)
        )}
      </div>

      {/* Assignment History */}
      <div
        className="rounded-xl p-6"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Assignment History</h2>
            <p className="text-[13px]" style={{ color: '#6b7280' }}>Previously released or auto-released assignments</p>
          </div>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-1 rounded-lg px-4 py-2 text-[13px] font-medium"
            style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#2B3990', cursor: 'pointer' }}
          >
            {showHistory ? 'Hide' : 'Show'} History
            {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {showHistory && (
          <div className="mt-4">
            {historyLoading ? (
              <div className="py-6 text-center text-[13px]" style={{ color: '#7C85C0' }}>Loading...</div>
            ) : releasedAssignments.length === 0 ? (
              <div className="py-6 text-center text-[13px]" style={{ color: '#7C85C0' }}>No assignment history.</div>
            ) : (
              renderTable(releasedAssignments, true)
            )}
          </div>
        )}
      </div>
    </div>
  )
}
