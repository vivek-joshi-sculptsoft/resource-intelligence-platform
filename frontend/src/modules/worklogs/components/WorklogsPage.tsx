import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, RotateCcw, Clock } from 'lucide-react'
import { fetchAllWorklogs, type WorklogEntry } from '../api'

const AVATAR_COLORS = ['#6366f1', '#f59e0b', '#22c55e', '#ec4899', '#8b5cf6', '#06b6d4', '#ef4444']
const PAGE_SIZE = 20

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

export function WorklogsPage() {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [page, setPage] = useState(1)
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['all-worklogs', startDate, endDate, page],
    queryFn: () =>
      fetchAllWorklogs({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        limit: PAGE_SIZE,
      }),
  })

  const entries: WorklogEntry[] = data?.data ?? []
  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const colorMap = useMemo(() => {
    const m = new Map<string, string>()
    let idx = 0
    entries.forEach((e) => {
      if (!m.has(e.resource.id)) {
        m.set(e.resource.id, AVATAR_COLORS[idx % AVATAR_COLORS.length])
        idx++
      }
    })
    return m
  }, [entries])

  function resetFilters() {
    setStartDate('')
    setEndDate('')
    setPage(1)
  }

  function toggleNote(id: string) {
    setExpandedNotes((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const totalHours = useMemo(
    () => entries.reduce((sum, e) => sum + Number(e.hours), 0),
    [entries],
  )

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1e1b4b', marginBottom: 4 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Clock size={22} /> Worklogs
          </span>
        </h1>
        <p style={{ fontSize: 14, color: '#6b7280' }}>
          View worklog entries across all projects
        </p>
      </div>

      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
          border: '1px solid #E8EAF6',
          overflow: 'hidden',
        }}
      >
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
          <button
            onClick={resetFilters}
            style={{
              marginLeft: 'auto',
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

        {/* Table */}
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>Loading...</div>
        ) : entries.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>&#128203;</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              No worklog entries found
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
                  {['Date', 'Resource', 'Project', 'Hours', 'Notes'].map((h) => (
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
                      <td style={{ padding: '12px 14px', fontSize: 14, borderBottom: '1px solid #E8EAF6' }}>
                        {w.project.name}
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
                            <span>
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

            {/* Footer with total + pagination */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 24px',
                borderTop: '1px solid #E8EAF6',
              }}
            >
              <div style={{ fontSize: 14, color: '#6b7280' }}>
                <span style={{ fontWeight: 600, color: '#2B3990' }}>{totalHours.toFixed(1)} hrs</span>
                {' '}on this page &middot; {total} total entries
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
