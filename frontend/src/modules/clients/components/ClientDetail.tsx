import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { useAuthStore } from '../../auth/store'
import { fetchClient, deleteClient } from '../api'
import { ClientFinancialsCard } from '../../financial/components/ClientFinancialsCard'
import { Breadcrumb } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'

export function ClientDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canEdit = user && ['CEO', 'CTO'].includes(user.role.code)

  const [showDeactivate, setShowDeactivate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['client', id],
    queryFn: () => fetchClient(id!),
    enabled: !!id,
  })

  const deactivateMut = useMutation({
    mutationFn: () => deleteClient(id!),
    onSuccess: () => { toast.success('Client deactivated'); queryClient.invalidateQueries({ queryKey: ['client', id] }); setShowDeactivate(false) },
    onError: (e: any) => toast.error(e.response?.data?.message || 'Failed to deactivate'),
  })

  const c = data?.data
  useDocumentTitle(c?.name)

  if (isLoading) return <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
  if (!c) return <div className="py-8 text-center text-[14px]" style={{ color: '#ef4444' }}>Client not found</div>

  return (
    <div>
      <Breadcrumb items={[{ label: 'Clients', to: '/clients' }, { label: c.name }]} />

      {/* Header Card */}
      <div className="mb-5 rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>{c.name}</h1>
            <div className="mt-1 flex items-center gap-3 text-[13.5px]" style={{ color: '#6b7280' }}>
              {c.industry && <span>{c.industry}</span>}
              {c.engagement_start_date && (
                <>
                  {c.industry && <span>·</span>}
                  <span>Since {new Date(c.engagement_start_date).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {canEdit && c.is_active && (
              <>
                <button onClick={() => navigate(`/clients/${c.id}/edit`)} className="rounded-lg px-5 py-2 text-[13.5px] font-semibold transition-all" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#2B3990' }}
                  onMouseEnter={(e) => { const t = e.currentTarget; t.style.background = '#2B3990'; t.style.color = '#fff' }}
                  onMouseLeave={(e) => { const t = e.currentTarget; t.style.background = '#fff'; t.style.color = '#2B3990' }}>Edit</button>
                <button onClick={() => setShowDeactivate(true)} className="rounded-lg px-5 py-2 text-[13.5px] font-semibold transition-all" style={{ border: '1px solid #fecaca', background: '#fff', color: '#ef4444' }}
                  onMouseEnter={(e) => { const t = e.currentTarget; t.style.background = '#ef4444'; t.style.color = '#fff' }}
                  onMouseLeave={(e) => { const t = e.currentTarget; t.style.background = '#fff'; t.style.color = '#ef4444' }}>Deactivate</button>
              </>
            )}
            {!c.is_active && <span className="inline-flex items-center rounded-full px-3 py-1 text-[12px] font-semibold" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>Inactive</span>}
          </div>
        </div>

        {/* Contact Info */}
        <div className="mt-4 grid grid-cols-3 gap-4 rounded-lg p-4" style={{ background: '#F0F1FA', border: '1px solid #E8EAF6' }}>
          <div>
            <div className="text-[11px] font-semibold uppercase" style={{ color: '#7C85C0' }}>Contact</div>
            <div className="mt-1 text-[13.5px] font-medium" style={{ color: '#1e1b4b' }}>{c.contact_name || '—'}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase" style={{ color: '#7C85C0' }}>Email</div>
            <div className="mt-1 text-[13.5px]" style={{ color: '#4A5BB5' }}>{c.contact_email || '—'}</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase" style={{ color: '#7C85C0' }}>Phone</div>
            <div className="mt-1 text-[13.5px]" style={{ color: '#1e1b4b' }}>{c.contact_phone || '—'}</div>
          </div>
        </div>

        {c.notes && (
          <div className="mt-4">
            <div className="text-[11px] font-semibold uppercase" style={{ color: '#7C85C0' }}>Notes</div>
            <p className="mt-1 text-[13.5px]" style={{ color: '#6b7280' }}>{c.notes}</p>
          </div>
        )}

        {/* Stats Row */}
        <div className="mt-5 flex gap-4">
          <div className="rounded-lg px-5 py-3" style={{ background: '#F0F1FA', border: '1px solid #E8EAF6' }}>
            <div className="text-[22px] font-bold" style={{ color: '#2B3990' }}>{c.dashboard.active_project_count}</div>
            <div className="text-[12px]" style={{ color: '#6b7280' }}>Active Projects</div>
          </div>
          <div className="rounded-lg px-5 py-3" style={{ background: '#F0F1FA', border: '1px solid #E8EAF6' }}>
            <div className="text-[22px] font-bold" style={{ color: '#2B3990' }}>{c.dashboard.active_resource_count}</div>
            <div className="text-[12px]" style={{ color: '#6b7280' }}>Active Resources</div>
          </div>
        </div>
      </div>

      {/* Financial Summary + Per-Project Breakdown — See VRIP-108 */}
      <ClientFinancialsCard clientId={c.id} />

      {/* Projects Table */}
      <div className="rounded-xl" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="px-6 pt-5 pb-3">
          <h2 className="text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Projects</h2>
        </div>
        {c.projects.length === 0 ? (
          <div className="px-6 pb-6 text-center text-[14px]" style={{ color: '#7C85C0' }}>No projects yet. Add a project for this client.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-[13.5px]">
              <thead>
                <tr>
                  {['Project Name', 'Type', 'Status'].map((h) => (
                    <th key={h} className="whitespace-nowrap px-4 py-[11px] text-[12px] font-semibold uppercase tracking-wide first:pl-6"
                      style={{ background: '#F0F1FA', color: '#7C85C0', borderBottom: '1px solid #E8EAF6' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {c.projects.map((p) => (
                  <tr key={p.id} className="cursor-pointer transition-colors"
                    style={{ borderBottom: '1px solid #E8EAF6' }}
                    onClick={() => navigate(`/projects/${p.id}`)}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#F0F1FA' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = '#fff' }}>
                    <td className="whitespace-nowrap px-4 py-[12px] pl-6 font-semibold" style={{ color: '#2B3990' }}>{p.name}</td>
                    <td className="whitespace-nowrap px-4 py-[12px]">
                      <span className="inline-block rounded-full px-2.5 py-[2px] text-[11px] font-semibold" style={{ background: '#E8EAF6', color: '#2B3990' }}>{p.type.replace(/_/g, ' ')}</span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-[12px]">
                      <span className="inline-flex items-center gap-[5px] rounded-full px-2.5 py-[2px] text-[11px] font-semibold"
                        style={{ background: p.status === 'ACTIVE' ? 'rgba(34,197,94,0.1)' : '#F0F1FA', color: p.status === 'ACTIVE' ? '#16a34a' : '#6b7280' }}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Deactivate modal */}
      {showDeactivate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.4)' }}>
          <div className="w-[420px] rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 16px 48px rgba(0,0,0,0.2)' }}>
            <h3 className="mb-2 text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Deactivate Client?</h3>
            <p className="mb-5 text-[14px]" style={{ color: '#6b7280' }}>This cannot be done if the client has active projects.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowDeactivate(false)} className="rounded-lg px-5 py-2 text-[13.5px] font-medium" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280', cursor: 'pointer' }}>Cancel</button>
              <button onClick={() => deactivateMut.mutate()} className="rounded-lg border-none px-5 py-2 text-[13.5px] font-semibold text-white" style={{ background: '#ef4444', cursor: 'pointer' }}>Deactivate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
