import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { useAuthStore } from '../../auth/store'
import { fetchResources, type ResourceListItem } from '../api'

function AvailabilityBadge({ pct }: { pct: number }) {
  if (pct === 0) return <span className="inline-block rounded-full px-2.5 py-[3px] text-[11px] font-semibold" style={{ background: '#fef3c7', color: '#92400e' }}>Bench</span>
  if (pct >= 100) return <span className="inline-block rounded-full px-2.5 py-[3px] text-[11px] font-semibold" style={{ background: pct > 100 ? '#fee2e2' : '#dcfce7', color: pct > 100 ? '#991b1b' : '#15803d' }}>{pct > 100 ? 'Over' : 'Full'}</span>
  return <span className="inline-block rounded-full px-2.5 py-[3px] text-[11px] font-semibold" style={{ background: '#dbeafe', color: '#1e40af' }}>Partial</span>
}

export function ResourceList() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const canCreate = user && ['CEO', 'CTO', 'HR'].includes(user.role.code)

  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ACTIVE')
  const [designation] = useState('')
  const [availability, setAvailability] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['resources', page, status, designation, availability, search],
    queryFn: () => fetchResources({
      page, limit: 20,
      status: status === 'ALL' ? undefined : status,
      designation: designation || undefined,
      availability: availability || undefined,
      search: search || undefined,
    }),
  })

  const resources = data?.data ?? []
  const meta = data?.meta

  return (
    <div>
      <div className="mb-1 text-[13px]" style={{ color: '#7C85C0' }}>
        Resources
      </div>

      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Resource Management</h1>
          <p className="mt-0.5 text-[13px]" style={{ color: '#6b7280' }}>Manage team members, skills, and availability</p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate('/resources/new')}
            className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white transition-all hover:-translate-y-px"
            style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Resource
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl p-4 px-5" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="relative min-w-[220px] flex-1">
          <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: '#7C85C0' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text" placeholder="Search by name or employee ID..."
            value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full rounded-lg py-[9px] pl-[38px] pr-3.5 text-[13.5px] outline-none transition-all"
            style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA' }}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.boxShadow = 'none'; e.target.style.background = '#F0F1FA' }}
          />
        </div>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none" style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA', appearance: 'none', backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%237C85C0' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}>
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
        <select value={availability} onChange={(e) => { setAvailability(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none" style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA', appearance: 'none', backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%237C85C0' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}>
          <option value="">All Availability</option>
          <option value="bench">Bench</option>
          <option value="partial">Partial</option>
          <option value="full">Fully Allocated</option>
        </select>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
      ) : resources.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl py-20 text-center" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="mb-4 text-[56px] opacity-70">&#128100;</div>
          <div className="mb-1.5 text-[18px] font-semibold" style={{ color: '#1e1b4b' }}>No resources found</div>
          <div className="mb-6 text-[14px]" style={{ color: '#6b7280' }}>Try adjusting filters or add a new resource.</div>
          {canCreate && (
            <button onClick={() => navigate('/resources/new')} className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white" style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
              Add Resource
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13.5px]">
              <thead>
                <tr>
                  {['Name', 'Employee ID', 'Designation', 'Expertise', 'Tags', 'Allocation', 'Availability', 'Status'].map((h) => (
                    <th key={h} className="whitespace-nowrap px-4 py-[13px] text-[12.5px] font-semibold uppercase tracking-wide text-white first:pl-5 last:pr-5"
                      style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)', letterSpacing: '0.3px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {resources.map((r: ResourceListItem, idx: number) => (
                  <tr key={r.id} className="cursor-pointer transition-colors"
                    style={{ borderBottom: '1px solid #E8EAF6', background: idx % 2 === 1 ? '#F5F6FC' : '#fff' }}
                    onClick={() => navigate(`/resources/${r.id}`)}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#E8EAF6' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = idx % 2 === 1 ? '#F5F6FC' : '#fff' }}>
                    <td className="whitespace-nowrap px-4 py-[13px] pl-5 font-semibold" style={{ color: '#2B3990' }}>{r.name}</td>
                    <td className="whitespace-nowrap px-4 py-[13px]" style={{ color: '#6b7280' }}>{r.employee_id}</td>
                    <td className="whitespace-nowrap px-4 py-[13px]" style={{ color: '#1e1b4b' }}>{r.designation}</td>
                    <td className="whitespace-nowrap px-4 py-[13px]" style={{ color: '#6b7280' }}>{r.technical_expertise || '—'}</td>
                    <td className="px-4 py-[13px]">
                      <div className="flex flex-wrap gap-1">
                        {r.tags.slice(0, 3).map((t) => (
                          <span key={t} className="inline-block rounded-full px-2 py-[2px] text-[10px] font-semibold" style={{ background: '#FFF0EC', color: '#FF4B2B' }}>{t}</span>
                        ))}
                        {r.tags.length > 3 && <span className="text-[10px] font-medium" style={{ color: '#7C85C0' }}>+{r.tags.length - 3}</span>}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-4 py-[13px] font-semibold" style={{ color: r.total_allocation_pct > 100 ? '#ef4444' : '#1e1b4b' }}>{r.total_allocation_pct}%</td>
                    <td className="whitespace-nowrap px-4 py-[13px]"><AvailabilityBadge pct={r.total_allocation_pct} /></td>
                    <td className="whitespace-nowrap px-4 py-[13px]">
                      <span className="inline-flex items-center gap-[5px] rounded-full px-3 py-1 text-[12px] font-semibold"
                        style={{ background: r.is_active ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: r.is_active ? '#16a34a' : '#ef4444' }}>
                        <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: r.is_active ? '#22c55e' : '#ef4444' }} />
                        {r.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {meta && (
            <div className="flex items-center justify-between px-5 py-3.5" style={{ borderTop: '1px solid #E8EAF6' }}>
              <span className="text-[13px]" style={{ color: '#6b7280' }}>
                Showing {(meta.page - 1) * meta.limit + 1}&ndash;{Math.min(meta.page * meta.limit, meta.total)} of {meta.total} resources
              </span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-md px-4 py-1.5 text-[13px] font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}>Prev</button>
                <button disabled={!meta || page >= meta.total_pages} onClick={() => setPage(page + 1)} className="rounded-md px-4 py-1.5 text-[13px] font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}>Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
