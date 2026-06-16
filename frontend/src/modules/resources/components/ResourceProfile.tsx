import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { useAuthStore } from '../../auth/store'
import { fetchResource, deleteResource, addResourceTag, removeResourceTag, updateResource } from '../api'
import { Breadcrumb } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'
import { ResourceAssignmentsPanel } from '../../allocations/components/ResourceAssignmentsPanel'

export function ResourceProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canEdit = user && ['CEO', 'CTO', 'HR'].includes(user.role.code)
  const canSeeCost = user && ['CEO', 'CTO', 'FINANCE'].includes(user.role.code)
  const canEditCost = canSeeCost

  const [tagInput, setTagInput] = useState('')
  const [showDeactivate, setShowDeactivate] = useState(false)
  const [editingCost, setEditingCost] = useState(false)
  const [costInput, setCostInput] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['resource', id],
    queryFn: () => fetchResource(id!),
    enabled: !!id,
  })

  const deactivateMut = useMutation({
    mutationFn: () => deleteResource(id!),
    onSuccess: () => { toast.success('Resource deactivated'); queryClient.invalidateQueries({ queryKey: ['resource', id] }); setShowDeactivate(false) },
    onError: (e: any) => toast.error(e.response?.data?.message || 'Failed to deactivate'),
  })

  const addTagMut = useMutation({
    mutationFn: (tag: string) => addResourceTag(id!, tag),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['resource', id] }); setTagInput('') },
  })

  const removeTagMut = useMutation({
    mutationFn: (tag: string) => removeResourceTag(id!, tag),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resource', id] }),
  })

  const updateCostMut = useMutation({
    mutationFn: (cost: number | null) => updateResource(id!, { loaded_cost_monthly: cost }),
    onSuccess: () => { toast.success('Cost updated'); queryClient.invalidateQueries({ queryKey: ['resource', id] }); setEditingCost(false) },
    onError: (e: any) => toast.error(e.response?.data?.message || 'Failed to update cost'),
  })

  const r = data?.data
  useDocumentTitle(r?.name)

  if (isLoading) return <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
  if (!r) return <div className="py-8 text-center text-[14px]" style={{ color: '#ef4444' }}>Resource not found</div>

  function availabilityLabel(pct: number) {
    if (pct === 0) return { text: 'On Bench', bg: '#fef3c7', color: '#92400e' }
    if (pct >= 100) return pct > 100 ? { text: 'Over-allocated', bg: '#fee2e2', color: '#991b1b' } : { text: 'Fully Allocated', bg: '#dcfce7', color: '#15803d' }
    return { text: 'Partially Allocated', bg: '#dbeafe', color: '#1e40af' }
  }

  const avail = availabilityLabel(r.total_allocation_pct)

  return (
    <div>
      <Breadcrumb items={[{ label: 'Resources', to: '/resources' }, { label: r.name }]} />

      {/* Header Card */}
      <div className="mb-5 rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>{r.name}</h1>
            <div className="mt-1 flex items-center gap-3 text-[13.5px]" style={{ color: '#6b7280' }}>
              <span>{r.employee_id}</span>
              <span>·</span>
              <span>{r.designation}</span>
              {r.technical_expertise && (<><span>·</span><span>{r.technical_expertise}</span></>)}
            </div>
            {r.reporting_manager && (
              <div className="mt-1.5 text-[13px]" style={{ color: '#7C85C0' }}>
                Reports to: <span className="cursor-pointer font-medium hover:underline" style={{ color: '#4A5BB5' }} onClick={() => navigate(`/resources/${r.reporting_manager!.id}`)}>{r.reporting_manager.name}</span>
              </div>
            )}
            {r.date_of_joining && (
              <div className="mt-1 text-[13px]" style={{ color: '#7C85C0' }}>
                Joined: {new Date(r.date_of_joining).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {canEdit && r.is_active && (
              <>
                <button onClick={() => navigate(`/resources/${r.id}/edit`)} className="rounded-lg px-5 py-2 text-[13.5px] font-semibold transition-all" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#2B3990' }}
                  onMouseEnter={(e) => { const t = e.currentTarget; t.style.background = '#2B3990'; t.style.color = '#fff' }}
                  onMouseLeave={(e) => { const t = e.currentTarget; t.style.background = '#fff'; t.style.color = '#2B3990' }}>Edit</button>
                <button onClick={() => setShowDeactivate(true)} className="rounded-lg px-5 py-2 text-[13.5px] font-semibold transition-all" style={{ border: '1px solid #fecaca', background: '#fff', color: '#ef4444' }}
                  onMouseEnter={(e) => { const t = e.currentTarget; t.style.background = '#ef4444'; t.style.color = '#fff' }}
                  onMouseLeave={(e) => { const t = e.currentTarget; t.style.background = '#fff'; t.style.color = '#ef4444' }}>Deactivate</button>
              </>
            )}
            {!r.is_active && <span className="inline-flex items-center rounded-full px-3 py-1 text-[12px] font-semibold" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>Inactive</span>}
          </div>
        </div>

        {/* Stats Row */}
        <div className="mt-5 flex gap-4">
          <div className="rounded-lg px-5 py-3" style={{ background: '#F0F1FA', border: '1px solid #E8EAF6' }}>
            <div className="text-[22px] font-bold" style={{ color: r.total_allocation_pct > 100 ? '#ef4444' : '#2B3990' }}>{r.total_allocation_pct}%</div>
            <div className="text-[12px]" style={{ color: '#6b7280' }}>Total Allocation</div>
          </div>
          <div className="flex items-center rounded-lg px-5 py-3" style={{ background: avail.bg }}>
            <span className="text-[13px] font-semibold" style={{ color: avail.color }}>{avail.text}</span>
          </div>
          {canSeeCost && (
            <div className="rounded-lg px-5 py-3" style={{ background: '#F0F1FA', border: '1px solid #E8EAF6' }}>
              <div className="text-[18px] font-bold" style={{ color: r.loaded_cost_monthly ? '#2B3990' : '#7C85C0' }}>
                {r.loaded_cost_monthly ? `₹${r.loaded_cost_monthly.toLocaleString('en-IN')}` : '—'}
              </div>
              <div className="text-[12px]" style={{ color: '#6b7280' }}>Loaded Cost (Monthly)</div>
            </div>
          )}
        </div>

        {/* Tags */}
        <div className="mt-4">
          <div className="mb-2 text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#7C85C0' }}>Tags</div>
          <div className="flex flex-wrap items-center gap-2">
            {r.tags.map((t) => (
              <span key={t} className="inline-flex items-center gap-1 rounded-full px-3 py-[3px] text-[11px] font-semibold" style={{ background: '#FFF0EC', color: '#FF4B2B' }}>
                {t}
                {canEdit && (
                  <button onClick={() => removeTagMut.mutate(t)} className="ml-0.5 border-none bg-transparent p-0 text-[14px] leading-none" style={{ color: '#FF4B2B', cursor: 'pointer' }}>&times;</button>
                )}
              </span>
            ))}
            {canEdit && (
              <form className="flex items-center gap-1" onSubmit={(e) => { e.preventDefault(); if (tagInput.trim()) addTagMut.mutate(tagInput.trim()) }}>
                <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} placeholder="Add tag..."
                  className="rounded-md px-2.5 py-[3px] text-[12px] outline-none" style={{ border: '1px solid #D6DAF0', width: '100px' }} />
                <button type="submit" className="rounded-md border-none px-2 py-[3px] text-[12px] font-medium" style={{ background: '#E8EAF6', color: '#2B3990', cursor: 'pointer' }}>+</button>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Cost Information — CEO/CTO/Finance only */}
      {canSeeCost && (
        <div className="mb-5 rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
          <div className="mb-3 flex items-center justify-between">
            <div className="text-[14px] font-bold" style={{ color: '#2B3990' }}>Cost Information</div>
            {canEditCost && !editingCost && r.is_active && (
              <button
                onClick={() => { setCostInput(r.loaded_cost_monthly ? String(r.loaded_cost_monthly) : ''); setEditingCost(true) }}
                className="rounded-md px-3 py-1 text-[12px] font-medium transition-colors"
                style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#2B3990', cursor: 'pointer' }}
              >
                Edit
              </button>
            )}
          </div>
          {editingCost ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <span className="text-[14px] font-medium" style={{ color: '#6b7280' }}>₹</span>
                <input
                  type="number"
                  value={costInput}
                  onChange={(e) => setCostInput(e.target.value)}
                  placeholder="e.g. 150000"
                  className="w-[200px] rounded-lg px-3 py-2 text-[13.5px] outline-none"
                  style={{ border: '1px solid #D6DAF0', background: '#F0F1FA' }}
                  onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
                  onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }}
                  autoFocus
                />
                <span className="text-[12px]" style={{ color: '#7C85C0' }}>/month</span>
              </div>
              <button
                onClick={() => updateCostMut.mutate(costInput ? parseFloat(costInput) : null)}
                disabled={updateCostMut.isPending}
                className="rounded-md border-none px-3 py-2 text-[12px] font-semibold text-white"
                style={{ background: '#FF4B2B', cursor: 'pointer' }}
              >
                {updateCostMut.isPending ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={() => setEditingCost(false)}
                className="rounded-md px-3 py-2 text-[12px] font-medium"
                style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280', cursor: 'pointer' }}
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="text-[15px] font-semibold" style={{ color: r.loaded_cost_monthly ? '#1e1b4b' : '#7C85C0' }}>
              {r.loaded_cost_monthly ? `₹${r.loaded_cost_monthly.toLocaleString('en-IN')} /month` : 'Not set'}
            </div>
          )}
        </div>
      )}

      {/* Assignments Panel */}
      <ResourceAssignmentsPanel resourceId={id!} />

      {/* Deactivate confirmation */}
      {showDeactivate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.4)' }}>
          <div className="w-[420px] rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 16px 48px rgba(0,0,0,0.2)' }}>
            <h3 className="mb-2 text-[16px] font-bold" style={{ color: '#1e1b4b' }}>Deactivate Resource?</h3>
            <p className="mb-5 text-[14px]" style={{ color: '#6b7280' }}>This will release all active assignments. This action cannot be undone easily.</p>
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
