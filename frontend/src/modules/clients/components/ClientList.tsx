import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { useAuthStore } from '../../auth/store'
import { fetchClients, type ClientListItem } from '../api'

export function ClientList() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const canCreate = user && ['CEO', 'CTO'].includes(user.role.code)

  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ACTIVE')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['clients', page, status, search],
    queryFn: () => fetchClients({
      page, limit: 20,
      status: status === 'ALL' ? undefined : status,
      search: search || undefined,
    }),
  })

  const clients = data?.data ?? []
  const meta = data?.meta

  return (
    <div>
      <div className="mb-1 text-[13px]" style={{ color: '#7C85C0' }}>Clients</div>

      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Client Management</h1>
          <p className="mt-0.5 text-[13px]" style={{ color: '#6b7280' }}>Manage client relationships and engagements</p>
        </div>
        {canCreate && (
          <button onClick={() => navigate('/clients/new')}
            className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white transition-all hover:-translate-y-px"
            style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Client
          </button>
        )}
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl p-4 px-5" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="relative min-w-[220px] flex-1">
          <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: '#7C85C0' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input type="text" placeholder="Search by client name..." value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full rounded-lg py-[9px] pl-[38px] pr-3.5 text-[13.5px] outline-none transition-all"
            style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA' }}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.boxShadow = 'none'; e.target.style.background = '#F0F1FA' }} />
        </div>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none"
          style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA', appearance: 'none', backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%237C85C0' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}>
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>

      {isLoading ? (
        <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
      ) : clients.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl py-20 text-center" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="mb-4 text-[56px] opacity-70">&#127970;</div>
          <div className="mb-1.5 text-[18px] font-semibold" style={{ color: '#1e1b4b' }}>No clients found</div>
          <div className="mb-6 text-[14px]" style={{ color: '#6b7280' }}>Add your first client to get started.</div>
          {canCreate && (
            <button onClick={() => navigate('/clients/new')} className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white" style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
              Add Client
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13.5px]">
              <thead>
                <tr>
                  {['Name', 'Industry', 'Engagement Start', 'Active Projects', 'Status'].map((h) => (
                    <th key={h} className="whitespace-nowrap px-4 py-[13px] text-[12.5px] font-semibold uppercase tracking-wide text-white first:pl-5 last:pr-5"
                      style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)', letterSpacing: '0.3px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {clients.map((c: ClientListItem, idx: number) => (
                  <tr key={c.id} className="cursor-pointer transition-colors"
                    style={{ borderBottom: '1px solid #E8EAF6', background: idx % 2 === 1 ? '#F5F6FC' : '#fff' }}
                    onClick={() => navigate(`/clients/${c.id}`)}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#E8EAF6' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = idx % 2 === 1 ? '#F5F6FC' : '#fff' }}>
                    <td className="whitespace-nowrap px-4 py-[13px] pl-5 font-semibold" style={{ color: '#2B3990' }}>{c.name}</td>
                    <td className="whitespace-nowrap px-4 py-[13px]" style={{ color: '#6b7280' }}>{c.industry || '—'}</td>
                    <td className="whitespace-nowrap px-4 py-[13px]" style={{ color: '#6b7280' }}>
                      {c.engagement_start_date ? new Date(c.engagement_start_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-[13px]">
                      <span className="inline-block rounded-full px-3 py-[3px] text-[12px] font-semibold" style={{ background: '#E8EAF6', color: '#2B3990' }}>{c.active_project_count}</span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-[13px]">
                      <span className="inline-flex items-center gap-[5px] rounded-full px-3 py-1 text-[12px] font-semibold"
                        style={{ background: c.is_active ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: c.is_active ? '#16a34a' : '#ef4444' }}>
                        <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: c.is_active ? '#22c55e' : '#ef4444' }} />
                        {c.is_active ? 'Active' : 'Inactive'}
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
                Showing {(meta.page - 1) * meta.limit + 1}&ndash;{Math.min(meta.page * meta.limit, meta.total)} of {meta.total} clients
              </span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-md px-4 py-1.5 text-[13px] font-medium disabled:cursor-not-allowed disabled:opacity-40" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}>Prev</button>
                <button disabled={!meta || page >= meta.total_pages} onClick={() => setPage(page + 1)} className="rounded-md px-4 py-1.5 text-[13px] font-medium disabled:cursor-not-allowed disabled:opacity-40" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}>Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
