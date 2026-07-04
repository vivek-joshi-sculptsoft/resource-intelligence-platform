import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, RotateCcw, Download } from 'lucide-react'
import { toast } from 'sonner'
import { fetchProjectWorklogs, exportProjectWorklogs, type WorklogEntry } from '../api'
import { fetchProjectAssignments, type AssignmentListItem } from '../../allocations/api'
import { SearchableSelect } from '../../../shared/components'

const AVATAR_COLORS = ['#6366f1', '#f59e0b', '#22c55e', '#ec4899', '#8b5cf6', '#06b6d4', '#ef4444']
const PAGE_SIZE = 15

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function displayDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

interface WorklogTabProps {
  projectId: string
}

export function WorklogTab({ projectId }: WorklogTabProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [resourceFilter, setResourceFilter] = useState('')
  const [page, setPage] = useState(1)
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set())
  const [exporting, setExporting] = useState(false)

  const { data: assignmentsData } = useQuery({
    queryKey: ['project-assignments-for-filter', projectId],
    queryFn: () => fetchProjectAssignments(projectId),
  })

  const resourceOptions = useMemo(() => {
    const assignments: AssignmentListItem[] = assignmentsData?.data ?? []
    const seen = new Map<string, string>()
    assignments.forEach((a) => {
      if (a.resource?.id && a.resource.name && !seen.has(a.resource.id)) {
        seen.set(a.resource.id, a.resource.name)
      }
    })
    return Array.from(seen.entries()).map(([id, name]) => ({ id, name }))
  }, [assignmentsData])

  const colorMap = useMemo(() => {
    const m = new Map<string, string>()
    resourceOptions.forEach((r, i) => m.set(r.id, AVATAR_COLORS[i % AVATAR_COLORS.length]))
    return m
  }, [resourceOptions])

  const { data, isLoading } = useQuery({
    queryKey: ['project-worklogs', projectId, startDate, endDate, resourceFilter, page],
    queryFn: () =>
      fetchProjectWorklogs(projectId, {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        resource_id: resourceFilter || undefined,
        page,
        limit: PAGE_SIZE,
      }),
  })

  const entries: WorklogEntry[] = data?.data ?? []
  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function resetFilters() {
    setStartDate('')
    setEndDate('')
    setResourceFilter('')
    setPage(1)
  }

  async function handleExport() {
    setExporting(true)
    try {
      await exportProjectWorklogs(projectId, {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        resource_id: resourceFilter || undefined,
      })
    } catch {
      toast.error('Export failed')
    } finally {
      setExporting(false)
    }
  }

  function toggleNote(id: string) {
    setExpandedNotes((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div>
      {/* Worklog Entries Card */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
          border: '1px solid #E8EAF6',
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
          <h3 style={{ fontSize: 15, fontWeight: 600 }}>Worklog Entries</h3>
        </div>

        {/* Filters */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'center',
            padding: '16px 24px',
            borderBottom: '1px solid #E8EAF6',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <label style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>From:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value)
                setPage(1)
              }}
              style={{
                padding: '7px 10px',
                border: '1px solid #D6DAF0',
                borderRadius: 8,
                fontSize: 13,
                color: '#1e1b4b',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <label style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>To:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value)
                setPage(1)
              }}
              style={{
                padding: '7px 10px',
                border: '1px solid #D6DAF0',
                borderRadius: 8,
                fontSize: 13,
                color: '#1e1b4b',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <label style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Resource:</label>
            <SearchableSelect
              value={resourceFilter}
              onChange={(v) => { setResourceFilter(v); setPage(1) }}
              options={[
                { value: '', label: 'All Resources' },
                ...resourceOptions.map((r) => ({ value: r.id, label: r.name })),
              ]}
              placeholder="All Resources"
              variant="filter"
            />
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button
              onClick={handleExport}
              disabled={exporting || isLoading || entries.length === 0}
              style={{
                padding: '8px 16px',
                border: '1px solid #D6DAF0',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                background: '#fff',
                cursor: exporting || isLoading || entries.length === 0 ? 'not-allowed' : 'pointer',
                opacity: exporting || isLoading || entries.length === 0 ? 0.5 : 1,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                color: '#2B3990',
              }}
            >
              <Download size={14} /> {exporting ? 'Exporting...' : 'Export'}
            </button>
            <button
              onClick={resetFilters}
              style={{
                padding: '8px 16px',
                border: '1px solid #D6DAF0',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                background: '#fff',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                color: '#1e1b4b',
              }}
            >
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>Loading...</div>
        ) : entries.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>&#128203;</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              No worklog entries for this period
            </div>
            <div style={{ fontSize: 14, color: '#6b7280' }}>
              Adjust your filters or wait for team members to log hours.
            </div>
          </div>
        ) : (
          <>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Date', 'Resource', 'Hours', 'Notes'].map((h) => (
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
                {entries.map((w, idx) => {
                  const avatarColor = colorMap.get(w.resource.id) ?? '#6366f1'
                  const isExpanded = expandedNotes.has(w.id)
                  const noteText = w.note ?? ''
                  const truncated = noteText.length > 60 && !isExpanded

                  return (
                    <tr
                      key={w.id}
                      style={{ background: idx % 2 === 1 ? '#F5F6FC' : '#fff' }}
                    >
                      <td
                        style={{
                          padding: '12px 14px',
                          fontSize: 14,
                          borderBottom: '1px solid #E8EAF6',
                          fontWeight: 600,
                        }}
                      >
                        {displayDate(w.log_date)}
                      </td>
                      <td style={{ padding: '12px 14px', fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div
                            style={{
                              width: 28,
                              height: 28,
                              borderRadius: '50%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: 11,
                              fontWeight: 600,
                              color: '#fff',
                              background: avatarColor,
                              flexShrink: 0,
                            }}
                          >
                            {getInitials(w.resource.name)}
                          </div>
                          {w.resource.name}
                        </div>
                      </td>
                      <td
                        style={{
                          padding: '12px 14px',
                          fontSize: 14,
                          fontWeight: 600,
                          borderBottom: '1px solid #E8EAF6',
                        }}
                      >
                        {w.hours}
                      </td>
                      <td
                        style={{
                          padding: '12px 14px',
                          fontSize: 13,
                          color: '#6b7280',
                          borderBottom: '1px solid #E8EAF6',
                          maxWidth: 280,
                        }}
                      >
                        {noteText ? (
                          <>
                            <span
                              style={{
                                ...(truncated
                                  ? {
                                      whiteSpace: 'nowrap' as const,
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      display: 'inline-block',
                                      maxWidth: 240,
                                      verticalAlign: 'bottom',
                                    }
                                  : {}),
                              }}
                            >
                              {truncated ? noteText.slice(0, 60) + '...' : noteText}
                            </span>
                            {noteText.length > 60 && (
                              <span
                                onClick={() => toggleNote(w.id)}
                                style={{
                                  color: '#2B3990',
                                  fontSize: 12,
                                  cursor: 'pointer',
                                  marginLeft: 4,
                                }}
                              >
                                {isExpanded ? 'less' : 'more'}
                              </span>
                            )}
                          </>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {/* Pagination */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 24px',
                borderTop: '1px solid #E8EAF6',
              }}
            >
              <div style={{ fontSize: 13, color: '#6b7280' }}>
                Showing {(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, total)} of {total}{' '}
                entries
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #D6DAF0',
                    borderRadius: 6,
                    background: '#fff',
                    cursor: page <= 1 ? 'not-allowed' : 'pointer',
                    opacity: page <= 1 ? 0.5 : 1,
                    fontSize: 13,
                    color: '#6b7280',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronLeft size={14} />
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (page <= 3) {
                    pageNum = i + 1
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = page - 2 + i
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      style={{
                        padding: '6px 10px',
                        border: `1px solid ${page === pageNum ? '#2B3990' : '#D6DAF0'}`,
                        borderRadius: 6,
                        background: page === pageNum ? '#2B3990' : '#fff',
                        color: page === pageNum ? '#fff' : '#6b7280',
                        cursor: 'pointer',
                        fontSize: 13,
                        minWidth: 32,
                      }}
                    >
                      {pageNum}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid #D6DAF0',
                    borderRadius: 6,
                    background: '#fff',
                    cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                    opacity: page >= totalPages ? 0.5 : 1,
                    fontSize: 13,
                    color: '#6b7280',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
