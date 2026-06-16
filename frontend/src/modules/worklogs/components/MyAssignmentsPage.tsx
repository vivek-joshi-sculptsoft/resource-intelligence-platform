import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuthStore } from '../../auth/store'
import { fetchResourceAssignments, type AssignmentListItem } from '../../allocations/api'
import {
  fetchMyWorklogs,
  createWorklog,
  updateWorklog,
  deleteWorklog,
  type WorklogEntry,
} from '../api'
import { ChevronLeft, ChevronRight, Clock, ClipboardList, Pencil, Trash2 } from 'lucide-react'

const ACCENT_COLORS = ['#2B3990', '#22c55e', '#7c3aed', '#f59e0b', '#ef4444', '#06b6d4']

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

function displayDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function dayLabel(d: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(d)
  target.setHours(0, 0, 0, 0)
  if (target.getTime() === today.getTime()) return 'Today'
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  if (target.getTime() === yesterday.getTime()) return 'Yesterday'
  return d.toLocaleDateString('en-IN', { weekday: 'long' })
}

function AllocationRing({ pct, color }: { pct: number; color: string }) {
  const r = 18
  const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 44, height: 44 }}>
        <svg viewBox="0 0 44 44" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="22" cy="22" r={r} fill="none" stroke="#E8EAF6" strokeWidth={4} />
          <circle
            cx="22"
            cy="22"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={4}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
          />
        </svg>
      </div>
      <div>
        <div style={{ fontSize: 18, fontWeight: 800, color: '#1e1b4b' }}>{pct}%</div>
        <div style={{ fontSize: 11, color: '#7C85C0' }}>Allocation</div>
      </div>
    </div>
  )
}

export function MyAssignmentsPage() {
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()
  const resourceId = user?.resource_id
  const isEngineer = user?.role?.code === 'ENGINEER'

  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    return d
  })
  const [editingEntry, setEditingEntry] = useState<WorklogEntry | null>(null)
  const [editHours, setEditHours] = useState<number>(0)
  const [editNote, setEditNote] = useState<string>('')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const today = useMemo(() => {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    return d
  }, [])

  const isFuture = selectedDate > today

  const { data: assignmentsData, isLoading: assignmentsLoading } = useQuery({
    queryKey: ['my-assignments', resourceId],
    queryFn: () => fetchResourceAssignments(resourceId!, 'ACTIVE'),
    enabled: !!resourceId,
  })

  const assignments: AssignmentListItem[] = assignmentsData?.data ?? []
  const worklogEnabledAssignments = assignments.filter(
    (a) => a.project?.worklog_enabled,
  )

  const totalAllocation = assignments.reduce((sum, a) => sum + a.allocation_pct, 0)

  const thirtyDaysAgo = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 30)
    return formatDate(d)
  }, [])

  const { data: recentData, isLoading: worklogsLoading } = useQuery({
    queryKey: ['my-worklogs-recent', resourceId, thirtyDaysAgo],
    queryFn: () =>
      fetchMyWorklogs({
        start_date: thirtyDaysAgo,
        limit: 50,
      }),
    enabled: !!resourceId,
  })

  const recentWorklogs: WorklogEntry[] = recentData?.data ?? []

  const dateStr = formatDate(selectedDate)
  const todaysLogs = useMemo(
    () => recentWorklogs.filter((w) => w.log_date === dateStr),
    [recentWorklogs, dateStr],
  )
  const loggedProjectIds = new Set(todaysLogs.map((w) => w.project.id))

  const [formRows, setFormRows] = useState<
    Record<string, { hours: string; note: string; saving: boolean; saved: boolean }>
  >({})

  const getFormRow = (projectId: string) =>
    formRows[projectId] ?? { hours: '', note: '', saving: false, saved: false }

  const setFormField = (projectId: string, field: 'hours' | 'note', value: string) => {
    setFormRows((prev) => ({
      ...prev,
      [projectId]: { ...getFormRow(projectId), [field]: value, saved: false },
    }))
  }

  const createMut = useMutation({
    mutationFn: createWorklog,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-worklogs-recent'] })
    },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { hours?: number; note?: string } }) =>
      updateWorklog(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-worklogs-recent'] })
      setEditingEntry(null)
      toast.success('Worklog updated')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      toast.error(msg || 'Update failed')
    },
  })

  const deleteMut = useMutation({
    mutationFn: deleteWorklog,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-worklogs-recent'] })
      setDeleteConfirm(null)
      toast.success('Worklog deleted')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      toast.error(msg || 'Delete failed')
    },
  })

  async function handleSaveRow(projectId: string) {
    const row = getFormRow(projectId)
    const hours = parseFloat(row.hours)
    if (!hours || hours < 0.5 || hours > 24 || (hours * 10) % 5 !== 0) {
      toast.error('Hours must be 0.5-24.0 in 0.5 increments')
      return
    }
    setFormRows((prev) => ({ ...prev, [projectId]: { ...row, saving: true } }))
    try {
      await createMut.mutateAsync({
        project_id: projectId,
        log_date: dateStr,
        hours,
        note: row.note || null,
      })
      setFormRows((prev) => ({
        ...prev,
        [projectId]: { hours: '', note: '', saving: false, saved: true },
      }))
      toast.success('Hours logged')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      toast.error(msg || 'Failed to log hours')
      setFormRows((prev) => ({ ...prev, [projectId]: { ...row, saving: false } }))
    }
  }

  function handleSaveAll() {
    const unloggedWithHours = worklogEnabledAssignments.filter((a) => {
      const pid = a.project?.id
      if (!pid || loggedProjectIds.has(pid)) return false
      const row = getFormRow(pid)
      return row.hours && parseFloat(row.hours) > 0
    })
    unloggedWithHours.forEach((a) => {
      if (a.project?.id) handleSaveRow(a.project.id)
    })
  }

  const totalFormHours = useMemo(() => {
    let total = 0
    todaysLogs.forEach((w) => (total += Number(w.hours)))
    worklogEnabledAssignments.forEach((a) => {
      const pid = a.project?.id
      if (!pid || loggedProjectIds.has(pid)) return
      const row = getFormRow(pid)
      if (row.hours) total += parseFloat(row.hours) || 0
    })
    return total
  }, [todaysLogs, worklogEnabledAssignments, formRows, loggedProjectIds])

  function prevDay() {
    setSelectedDate((prev) => {
      const d = new Date(prev)
      d.setDate(d.getDate() - 1)
      return d
    })
  }

  function nextDay() {
    if (!isFuture) {
      setSelectedDate((prev) => {
        const d = new Date(prev)
        d.setDate(d.getDate() + 1)
        if (d > today) return prev
        return d
      })
    }
  }

  if (!resourceId) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>&#128100;</div>
        <h3 style={{ fontSize: 18, color: '#1e1b4b', marginBottom: 8 }}>No Resource Profile</h3>
        <p style={{ fontSize: 14, color: '#6b7280', maxWidth: 400, margin: '0 auto' }}>
          Your account is not linked to a resource profile. Contact your admin to set up your resource profile.
        </p>
      </div>
    )
  }

  if (!isEngineer) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>&#128100;</div>
        <h3 style={{ fontSize: 18, color: '#1e1b4b', marginBottom: 8 }}>Engineer View</h3>
        <p style={{ fontSize: 14, color: '#6b7280', maxWidth: 400, margin: '0 auto' }}>
          My Assignments is designed for engineers to see their own project assignments. Use the Dashboard or Availability pages for your role.
        </p>
      </div>
    )
  }

  if (assignmentsLoading) {
    return (
      <div style={{ padding: '40px 0' }}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              height: 120,
              background: '#E8EAF6',
              borderRadius: 12,
              marginBottom: 16,
              animation: 'pulse 1.5s ease-in-out infinite',
            }}
          />
        ))}
      </div>
    )
  }

  if (assignments.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>&#128203;</div>
        <h3 style={{ fontSize: 16, color: '#1e1b4b', marginBottom: 6 }}>
          You have no active project assignments
        </h3>
        <p style={{ fontSize: 13, color: '#6b7280' }}>
          When you are assigned to a project, your assignments will appear here with project details and allocation information.
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* Welcome Card */}
      <div
        style={{
          background: 'linear-gradient(135deg, #2B3990 0%, #4A5BB5 60%, #6366f1 100%)',
          borderRadius: 12,
          padding: '24px 28px',
          marginBottom: 24,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
            Welcome back, {user?.name?.split(' ')[0]}!
          </h2>
          <p style={{ fontSize: 14, opacity: 0.85 }}>
            Here are your active project assignments.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{assignments.length}</div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, opacity: 0.75 }}>
              Active Projects
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{totalAllocation}%</div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, opacity: 0.75 }}>
              Total Allocation
            </div>
          </div>
        </div>
      </div>

      {/* Total Allocation Bar */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Total Allocation</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#2B3990' }}>
            {totalAllocation}% allocated &middot; {Math.max(0, 100 - totalAllocation)}% available
          </span>
        </div>
        <div style={{ height: 10, background: '#E8EAF6', borderRadius: 5, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              borderRadius: 5,
              background: 'linear-gradient(90deg, #2B3990, #4A5BB5)',
              width: `${Math.min(totalAllocation, 100)}%`,
              transition: 'width 0.6s ease',
            }}
          />
        </div>
      </div>

      {/* Assignment Cards */}
      <div style={{ marginBottom: 8 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>My Active Assignments</h1>
        <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>
          Your current project assignments and allocation details
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
          gap: 16,
          marginBottom: 32,
        }}
      >
        {assignments.map((a, idx) => {
          const color = ACCENT_COLORS[idx % ACCENT_COLORS.length]
          const project = a.project
          return (
            <div
              key={a.id}
              style={{
                background: '#fff',
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
                border: '1px solid #E8EAF6',
                overflow: 'hidden',
                transition: 'box-shadow 0.2s, transform 0.2s',
                cursor: 'default',
              }}
              onMouseEnter={(e) => {
                ;(e.currentTarget as HTMLElement).style.boxShadow = '0 6px 20px rgba(43,57,144,0.12)'
                ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget as HTMLElement).style.boxShadow =
                  '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)'
                ;(e.currentTarget as HTMLElement).style.transform = 'none'
              }}
            >
              <div style={{ height: 4, background: `linear-gradient(90deg, ${color}, ${color}88)` }} />
              <div style={{ padding: 20 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#1e1b4b', marginBottom: 4 }}>
                  {project?.name ?? 'Unknown Project'}
                </div>
                <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
                  {project?.client_name ?? ''}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        marginBottom: 2,
                        fontWeight: 600,
                      }}
                    >
                      My Role
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#1e1b4b' }}>
                      {a.effective_designation ?? a.resource?.designation ?? 'Developer'}
                    </div>
                  </div>
                  <AllocationRing pct={a.allocation_pct} color={color} />
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        marginBottom: 2,
                        fontWeight: 600,
                      }}
                    >
                      Start Date
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#1e1b4b' }}>
                      {displayDate(a.start_date)}
                    </div>
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        marginBottom: 2,
                        fontWeight: 600,
                      }}
                    >
                      End Date
                    </div>
                    <div
                      style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: a.end_date ? '#1e1b4b' : '#22c55e',
                      }}
                    >
                      {a.end_date ? displayDate(a.end_date) : 'Ongoing'}
                    </div>
                  </div>
                </div>
                {project?.worklog_enabled && (
                  <a
                    href="#worklog-section"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      marginTop: 16,
                      padding: '8px 14px',
                      background: '#F0F1FA',
                      borderRadius: 8,
                      color: '#2B3990',
                      fontSize: 13,
                      fontWeight: 600,
                      textDecoration: 'none',
                      border: '1px solid #E8EAF6',
                      transition: 'all 0.15s',
                    }}
                    onMouseEnter={(e) => {
                      ;(e.currentTarget as HTMLElement).style.background = '#2B3990'
                      ;(e.currentTarget as HTMLElement).style.color = '#fff'
                      ;(e.currentTarget as HTMLElement).style.borderColor = '#2B3990'
                    }}
                    onMouseLeave={(e) => {
                      ;(e.currentTarget as HTMLElement).style.background = '#F0F1FA'
                      ;(e.currentTarget as HTMLElement).style.color = '#2B3990'
                      ;(e.currentTarget as HTMLElement).style.borderColor = '#E8EAF6'
                    }}
                  >
                    <Clock size={14} /> Log Hours
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Worklog Entry Section ── */}
      <div id="worklog-section">
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Log Hours</h1>
        <p style={{ fontSize: 14, color: '#6b7280', marginBottom: 24 }}>
          Record your daily work hours against active project assignments
        </p>

        {worklogEnabledAssignments.length === 0 ? (
          <div
            style={{
              background: '#fff',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(43,57,144,0.06)',
              border: '1px solid #E8EAF6',
              padding: '48px 24px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 12 }}>&#128203;</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              No projects with worklog enabled
            </div>
            <div style={{ fontSize: 14, color: '#6b7280' }}>
              Ask your manager to enable worklog for your project.
            </div>
          </div>
        ) : (
          <>
            {/* Date Selector */}
            <div
              style={{
                background: '#fff',
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(43,57,144,0.06)',
                border: '1px solid #E8EAF6',
                marginBottom: 20,
                padding: '20px 24px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ fontSize: 14, fontWeight: 500 }}>Date:</label>
                <button
                  onClick={prevDay}
                  title="Previous day"
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #D6DAF0',
                    borderRadius: 8,
                    background: '#fff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronLeft size={16} />
                </button>
                <input
                  type="date"
                  value={dateStr}
                  max={formatDate(today)}
                  onChange={(e) => {
                    const d = new Date(e.target.value + 'T00:00:00')
                    if (d <= today) setSelectedDate(d)
                  }}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #D6DAF0',
                    borderRadius: 8,
                    fontSize: 14,
                    color: '#1e1b4b',
                  }}
                />
                <button
                  onClick={nextDay}
                  disabled={selectedDate >= today}
                  title="Next day"
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #D6DAF0',
                    borderRadius: 8,
                    background: '#fff',
                    cursor: selectedDate >= today ? 'not-allowed' : 'pointer',
                    opacity: selectedDate >= today ? 0.4 : 1,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronRight size={16} />
                </button>
                <span style={{ fontSize: 13, color: '#7C85C0', marginLeft: 4 }}>
                  {dayLabel(selectedDate)} ({selectedDate.toLocaleDateString('en-IN', { weekday: 'long' })})
                </span>
              </div>
            </div>

            {/* Active Assignments Table */}
            <div
              style={{
                background: '#fff',
                borderRadius: 12,
                boxShadow: '0 2px 8px rgba(43,57,144,0.06)',
                border: '1px solid #E8EAF6',
                marginBottom: 20,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  padding: '18px 24px',
                  borderBottom: '1px solid #E8EAF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <h3 style={{ fontSize: 15, fontWeight: 600 }}>Active Assignments</h3>
                <span style={{ fontSize: 13, color: '#6b7280' }}>
                  {worklogEnabledAssignments.length} worklog-enabled projects
                </span>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                        width: '28%',
                      }}
                    >
                      Project
                    </th>
                    <th
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                        width: '18%',
                      }}
                    >
                      Designation
                    </th>
                    <th
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                        width: '14%',
                      }}
                    >
                      Hours
                    </th>
                    <th
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                        width: '34%',
                      }}
                    >
                      Notes
                    </th>
                    <th
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                        width: '6%',
                      }}
                    >
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {worklogEnabledAssignments.map((a, idx) => {
                    const pid = a.project?.id
                    if (!pid) return null
                    const existingLog = todaysLogs.find((w) => w.project.id === pid)
                    const color = ACCENT_COLORS[assignments.indexOf(a) % ACCENT_COLORS.length]
                    const row = getFormRow(pid)

                    return (
                      <tr
                        key={pid}
                        style={{
                          background: idx % 2 === 1 ? '#F5F6FC' : '#fff',
                        }}
                      >
                        <td style={{ padding: 14, fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span
                              style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: color,
                                flexShrink: 0,
                              }}
                            />
                            <strong>{a.project?.name}</strong>
                          </div>
                          <div
                            style={{
                              fontSize: 12,
                              color: '#6b7280',
                              marginTop: 2,
                              paddingLeft: 14,
                            }}
                          >
                            Client: {a.project?.client_name ?? 'N/A'}
                          </div>
                        </td>
                        <td style={{ padding: 14, fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                          {a.effective_designation ?? a.resource?.designation ?? '-'}
                        </td>
                        <td style={{ padding: 14, borderBottom: '1px solid #E8EAF6' }}>
                          {existingLog ? (
                            <span style={{ fontWeight: 600, fontSize: 14 }}>{existingLog.hours}</span>
                          ) : (
                            <input
                              type="number"
                              min="0.5"
                              max="24"
                              step="0.5"
                              value={row.hours}
                              onChange={(e) => setFormField(pid, 'hours', e.target.value)}
                              placeholder="0.0"
                              style={{
                                width: 80,
                                padding: '8px 10px',
                                border: '1px solid #D6DAF0',
                                borderRadius: 8,
                                fontSize: 14,
                                textAlign: 'center',
                              }}
                            />
                          )}
                        </td>
                        <td style={{ padding: 14, borderBottom: '1px solid #E8EAF6' }}>
                          {existingLog ? (
                            <span style={{ fontSize: 13, color: '#6b7280' }}>
                              {existingLog.note || '-'}
                            </span>
                          ) : (
                            <textarea
                              rows={1}
                              placeholder="What did you work on?"
                              value={row.note}
                              onChange={(e) => setFormField(pid, 'note', e.target.value)}
                              style={{
                                width: '100%',
                                minHeight: 36,
                                padding: '8px 10px',
                                border: '1px solid #D6DAF0',
                                borderRadius: 8,
                                fontSize: 13,
                                resize: 'vertical',
                                fontFamily: 'inherit',
                              }}
                            />
                          )}
                        </td>
                        <td style={{ padding: 14, borderBottom: '1px solid #E8EAF6' }}>
                          {existingLog ? (
                            <span
                              style={{
                                display: 'inline-flex',
                                padding: '3px 10px',
                                borderRadius: 20,
                                fontSize: 12,
                                fontWeight: 500,
                                background: '#dcfce7',
                                color: '#166534',
                              }}
                            >
                              Saved
                            </span>
                          ) : row.saved ? (
                            <span
                              style={{
                                display: 'inline-flex',
                                padding: '3px 10px',
                                borderRadius: 20,
                                fontSize: 12,
                                fontWeight: 500,
                                background: '#dcfce7',
                                color: '#166534',
                              }}
                            >
                              Saved
                            </span>
                          ) : null}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <div
                style={{
                  padding: '18px 24px',
                  borderTop: '1px solid #E8EAF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ fontSize: 16, fontWeight: 700, color: '#2B3990' }}>
                  Total: {totalFormHours.toFixed(1)} hrs{' '}
                  <span style={{ fontSize: 13, fontWeight: 400, color: '#6b7280' }}>/ 8 hrs standard</span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    onClick={handleSaveAll}
                    disabled={isFuture}
                    style={{
                      padding: '10px 20px',
                      border: 'none',
                      borderRadius: 8,
                      fontSize: 14,
                      fontWeight: 600,
                      cursor: isFuture ? 'not-allowed' : 'pointer',
                      background: '#FF4B2B',
                      color: '#fff',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      opacity: isFuture ? 0.5 : 1,
                    }}
                  >
                    <ClipboardList size={16} /> Save Worklogs
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Recent Entries */}
        <div
          style={{
            background: '#fff',
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(43,57,144,0.06)',
            border: '1px solid #E8EAF6',
            marginBottom: 20,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '18px 24px',
              borderBottom: '1px solid #E8EAF6',
            }}
          >
            <h3 style={{ fontSize: 15, fontWeight: 600 }}>Recent Entries (Last 30 Days)</h3>
          </div>
          {worklogsLoading ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>Loading...</div>
          ) : recentWorklogs.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#6b7280', fontSize: 14 }}>
              No worklog entries yet. Start logging hours above.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Date', 'Project', 'Hours', 'Note', 'Actions'].map((h) => (
                    <th
                      key={h}
                      style={{
                        textAlign: 'left',
                        fontSize: 12,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        color: '#7C85C0',
                        padding: '10px 14px',
                        borderBottom: '2px solid #D6DAF0',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentWorklogs.map((w, idx) => {
                  const projAssignment = assignments.find((a) => a.project?.id === w.project.id)
                  const color =
                    ACCENT_COLORS[
                      projAssignment ? assignments.indexOf(projAssignment) % ACCENT_COLORS.length : 0
                    ]
                  return (
                    <tr
                      key={w.id}
                      style={{ background: idx % 2 === 1 ? '#F5F6FC' : '#fff' }}
                    >
                      <td style={{ padding: 14, fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                        {displayDate(w.log_date)}
                      </td>
                      <td style={{ padding: 14, fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          <span
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              background: color,
                            }}
                          />
                          {w.project.name}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: 14,
                          fontSize: 14,
                          fontWeight: 600,
                          borderBottom: '1px solid #E8EAF6',
                        }}
                      >
                        {w.hours}
                      </td>
                      <td
                        style={{
                          padding: 14,
                          fontSize: 13,
                          color: '#6b7280',
                          borderBottom: '1px solid #E8EAF6',
                        }}
                      >
                        {w.note || '-'}
                      </td>
                      <td style={{ padding: 14, borderBottom: '1px solid #E8EAF6' }}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => {
                              setEditingEntry(w)
                              setEditHours(w.hours)
                              setEditNote(w.note ?? '')
                            }}
                            style={{
                              padding: '6px 12px',
                              fontSize: 13,
                              fontWeight: 600,
                              border: '1px solid #D6DAF0',
                              borderRadius: 8,
                              background: '#fff',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              color: '#1e1b4b',
                            }}
                          >
                            <Pencil size={13} /> Edit
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(w.id)}
                            style={{
                              padding: '6px 12px',
                              fontSize: 13,
                              fontWeight: 600,
                              border: '1px solid #D6DAF0',
                              borderRadius: 8,
                              background: '#fff',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              color: '#ef4444',
                            }}
                          >
                            <Trash2 size={13} /> Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {editingEntry && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
          }}
          onClick={() => setEditingEntry(null)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 12,
              padding: 24,
              width: 420,
              maxWidth: '90%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Edit Worklog</h3>
            <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>
              {editingEntry.project.name} &middot; {displayDate(editingEntry.log_date)}
            </p>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Hours
              </label>
              <input
                type="number"
                min="0.5"
                max="24"
                step="0.5"
                value={editHours}
                onChange={(e) => setEditHours(parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #D6DAF0',
                  borderRadius: 8,
                  fontSize: 14,
                }}
              />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Note
              </label>
              <textarea
                rows={3}
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #D6DAF0',
                  borderRadius: 8,
                  fontSize: 14,
                  fontFamily: 'inherit',
                  resize: 'vertical',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditingEntry(null)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #D6DAF0',
                  borderRadius: 8,
                  background: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (!editHours || editHours < 0.5 || editHours > 24 || (editHours * 10) % 5 !== 0) {
                    toast.error('Hours must be 0.5-24.0 in 0.5 increments')
                    return
                  }
                  updateMut.mutate({
                    id: editingEntry.id,
                    payload: { hours: editHours, note: editNote || undefined },
                  })
                }}
                disabled={updateMut.isPending}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: 8,
                  background: '#FF4B2B',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {updateMut.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
          }}
          onClick={() => setDeleteConfirm(null)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 12,
              padding: 24,
              width: 380,
              maxWidth: '90%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, color: '#ef4444' }}>
              Delete Worklog Entry
            </h3>
            <p style={{ fontSize: 14, color: '#6b7280', marginBottom: 20 }}>
              Are you sure? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setDeleteConfirm(null)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #D6DAF0',
                  borderRadius: 8,
                  background: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => deleteMut.mutate(deleteConfirm)}
                disabled={deleteMut.isPending}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: 8,
                  background: '#ef4444',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {deleteMut.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
