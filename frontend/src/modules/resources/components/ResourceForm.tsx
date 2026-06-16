import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { useAuthStore } from '../../auth/store'
import { createResource, fetchResource, fetchResourcesDropdown, updateResource } from '../api'

function ManagerSearchSelect({
  managers,
  value,
  onChange,
  currentResourceId,
}: {
  managers: { id: string; name: string; employee_id: string }[]
  value: string
  onChange: (id: string) => void
  currentResourceId?: string
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  const available = managers.filter((m) => m.id !== currentResourceId)
  const selected = available.find((m) => m.id === value)
  const filtered = available.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.employee_id.toLowerCase().includes(search.toLowerCase()),
  )

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => { setOpen(!open); setSearch('') }}
        className="w-full rounded-lg px-3.5 py-[9px] text-left text-[13.5px] outline-none"
        style={{
          border: '1px solid #D6DAF0',
          background: '#F0F1FA',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          color: selected ? '#1e1b4b' : '#9ca3af',
        }}
      >
        <span className="truncate">
          {selected ? `${selected.name} (${selected.employee_id})` : 'None'}
        </span>
        <div className="flex items-center gap-1.5">
          {selected && (
            <span
              onClick={(e) => { e.stopPropagation(); onChange(''); setOpen(false) }}
              className="flex items-center justify-center rounded-full transition-colors hover:bg-[#E8EAF6]"
              style={{ width: 18, height: 18, color: '#7C85C0', cursor: 'pointer' }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </span>
          )}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7C85C0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {open && (
        <div
          className="absolute left-0 right-0 z-50 mt-1 overflow-hidden rounded-lg"
          style={{ background: '#fff', border: '1.5px solid #D6DAF0', boxShadow: '0 4px 16px rgba(43,57,144,0.12)' }}
        >
          {available.length > 3 && (
            <div className="p-2">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name or ID..."
                autoFocus
                className="w-full rounded-md px-3 py-[7px] text-[13px] outline-none"
                style={{ border: '1px solid #D6DAF0', color: '#1e1b4b' }}
                onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)' }}
                onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.boxShadow = 'none' }}
              />
            </div>
          )}
          <div className="max-h-[200px] overflow-y-auto">
            <button
              type="button"
              onClick={() => { onChange(''); setOpen(false); setSearch('') }}
              className="w-full border-none px-3 py-2 text-left text-[13px] transition-colors hover:bg-[#F0F1FA]"
              style={{ background: !value ? '#EEF0FF' : 'transparent', color: '#6b7280', cursor: 'pointer' }}
            >
              None
            </button>
            {filtered.map((m) => (
              <button
                type="button"
                key={m.id}
                onClick={() => { onChange(m.id); setOpen(false); setSearch('') }}
                className="w-full border-none px-3 py-2 text-left text-[13px] transition-colors hover:bg-[#F0F1FA]"
                style={{ background: m.id === value ? '#EEF0FF' : 'transparent', color: '#1e1b4b', cursor: 'pointer' }}
              >
                {m.name} <span style={{ color: '#7C85C0' }}>({m.employee_id})</span>
              </button>
            ))}
            {available.length > 0 && filtered.length === 0 && (
              <div className="px-3 py-3 text-center text-[13px]" style={{ color: '#7C85C0' }}>
                No resources found
              </div>
            )}
            {available.length === 0 && (
              <div className="px-3 py-3 text-center text-[13px]" style={{ color: '#7C85C0' }}>
                No other resources available
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function ResourceForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canEditCost = user && ['CEO', 'CTO', 'FINANCE'].includes(user.role.code)

  const [form, setForm] = useState({
    employee_id: '',
    name: '',
    designation: '',
    technical_expertise: '',
    date_of_joining: '',
    reporting_manager_id: '',
    tags: [] as string[],
    loaded_cost_monthly: '',
  })
  const [tagInput, setTagInput] = useState('')
  const [error, setError] = useState<{ message: string; field?: string } | null>(null)

  const { data: resourceData } = useQuery({
    queryKey: ['resource', id],
    queryFn: () => fetchResource(id!),
    enabled: isEdit,
  })

  const { data: managers } = useQuery({
    queryKey: ['resources-dropdown'],
    queryFn: fetchResourcesDropdown,
  })

  useEffect(() => {
    if (isEdit && resourceData?.data) {
      const r = resourceData.data
      setForm({
        employee_id: r.employee_id,
        name: r.name,
        designation: r.designation,
        technical_expertise: r.technical_expertise || '',
        date_of_joining: r.date_of_joining || '',
        reporting_manager_id: r.reporting_manager?.id || '',
        tags: r.tags,
        loaded_cost_monthly: r.loaded_cost_monthly ? String(r.loaded_cost_monthly) : '',
      })
    }
  }, [isEdit, resourceData])

  const createMut = useMutation({
    mutationFn: () => createResource({
      employee_id: form.employee_id,
      name: form.name,
      designation: form.designation,
      technical_expertise: form.technical_expertise || undefined,
      date_of_joining: form.date_of_joining || undefined,
      reporting_manager_id: form.reporting_manager_id || null,
      tags: form.tags,
      ...(canEditCost && form.loaded_cost_monthly ? { loaded_cost_monthly: parseFloat(form.loaded_cost_monthly) } : {}),
    }),
    onSuccess: (data) => {
      toast.success('Resource created')
      queryClient.invalidateQueries({ queryKey: ['resources'] })
      navigate(`/resources/${data.data.id}`)
    },
    onError: (e: any) => {
      const msg = e.response?.data?.message || 'Failed to create'
      const field = e.response?.data?.field
      setError({ message: msg, field })
    },
  })

  const updateMut = useMutation({
    mutationFn: () => updateResource(id!, {
      employee_id: form.employee_id,
      name: form.name,
      designation: form.designation,
      technical_expertise: form.technical_expertise || undefined,
      date_of_joining: form.date_of_joining || undefined,
      reporting_manager_id: form.reporting_manager_id || null,
      ...(canEditCost ? { loaded_cost_monthly: form.loaded_cost_monthly ? parseFloat(form.loaded_cost_monthly) : null } : {}),
    }),
    onSuccess: () => {
      toast.success('Resource updated')
      queryClient.invalidateQueries({ queryKey: ['resource', id] })
      queryClient.invalidateQueries({ queryKey: ['resources'] })
      navigate(`/resources/${id}`)
    },
    onError: (e: any) => {
      const msg = e.response?.data?.message || 'Failed to update'
      const field = e.response?.data?.field
      setError({ message: msg, field })
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!form.name || !form.employee_id || !form.designation) {
      setError({ message: 'Name, Employee ID, and Designation are required' })
      return
    }
    isEdit ? updateMut.mutate() : createMut.mutate()
  }

  function addTag() {
    const t = tagInput.trim()
    if (t && !form.tags.includes(t)) {
      setForm({ ...form, tags: [...form.tags, t] })
      setTagInput('')
    }
  }

  const inputStyle = { border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA' }
  const labelStyle = { color: '#1e1b4b', fontSize: '13.5px', fontWeight: 600 as const, marginBottom: '4px', display: 'block' as const }

  return (
    <div>
      <div className="mb-1 text-[13px]" style={{ color: '#7C85C0' }}>
        <span className="cursor-pointer hover:underline" onClick={() => navigate('/resources')}>Resources</span>
        <span style={{ color: '#6b7280' }}> &rsaquo; </span>
        <span style={{ color: '#6b7280' }}>{isEdit ? 'Edit Resource' : 'Add Resource'}</span>
      </div>

      <h1 className="mb-5 text-[22px] font-bold" style={{ color: '#1e1b4b' }}>{isEdit ? 'Edit Resource' : 'Add Resource'}</h1>

      <form onSubmit={handleSubmit} className="mx-auto max-w-[640px] rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        {error && (
          <div className="mb-4 rounded-lg px-4 py-3 text-[13.5px] font-medium" style={{ background: '#fef2f2', color: '#ef4444', border: '1px solid #fecaca' }}>
            {error.message}
          </div>
        )}

        <div className="mb-4">
          <label style={labelStyle}>Name <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
        </div>

        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label style={labelStyle}>Employee ID <span style={{ color: '#ef4444' }}>*</span></label>
            <input type="text" value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={{ ...inputStyle, borderColor: error?.field === 'employee_id' ? '#ef4444' : '#D6DAF0' }}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = error?.field === 'employee_id' ? '#ef4444' : '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
          <div>
            <label style={labelStyle}>Designation <span style={{ color: '#ef4444' }}>*</span></label>
            <input type="text" value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label style={labelStyle}>Technical Expertise</label>
            <input type="text" value={form.technical_expertise} onChange={(e) => setForm({ ...form, technical_expertise: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
          <div>
            <label style={labelStyle}>Date of Joining</label>
            <input type="date" value={form.date_of_joining} onChange={(e) => setForm({ ...form, date_of_joining: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
        </div>

        <div className="mb-4">
          <label style={labelStyle}>Reporting Manager</label>
          <ManagerSearchSelect
            managers={managers || []}
            value={form.reporting_manager_id}
            onChange={(val) => setForm({ ...form, reporting_manager_id: val })}
            currentResourceId={id}
          />
        </div>

        {canEditCost && (
          <div className="mb-4">
            <label style={labelStyle}>Loaded Cost Monthly (INR)</label>
            <input type="number" value={form.loaded_cost_monthly} onChange={(e) => setForm({ ...form, loaded_cost_monthly: e.target.value })}
              placeholder="e.g. 150000" step="0.01" min="0"
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
            <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>CTC + overhead per month. Visible to CEO, CTO, and Finance only.</div>
          </div>
        )}

        {!isEdit && (
          <div className="mb-5">
            <label style={labelStyle}>Tags</label>
            <div className="flex flex-wrap items-center gap-2">
              {form.tags.map((t) => (
                <span key={t} className="inline-flex items-center gap-1 rounded-full px-3 py-[3px] text-[11px] font-semibold" style={{ background: '#FFF0EC', color: '#FF4B2B' }}>
                  {t}
                  <button type="button" onClick={() => setForm({ ...form, tags: form.tags.filter(x => x !== t) })} className="ml-0.5 border-none bg-transparent p-0 text-[14px] leading-none" style={{ color: '#FF4B2B', cursor: 'pointer' }}>&times;</button>
                </span>
              ))}
              <div className="flex items-center gap-1">
                <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} placeholder="Add tag..." onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag() } }}
                  className="rounded-md px-2.5 py-[3px] text-[12px] outline-none" style={{ border: '1px solid #D6DAF0', width: '100px' }} />
                <button type="button" onClick={addTag} className="rounded-md border-none px-2 py-[3px] text-[12px] font-medium" style={{ background: '#E8EAF6', color: '#2B3990', cursor: 'pointer' }}>+</button>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2" style={{ borderTop: '1px solid #E8EAF6' }}>
          <button type="button" onClick={() => navigate(isEdit ? `/resources/${id}` : '/resources')}
            className="rounded-lg px-6 py-2.5 text-[13.5px] font-medium" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280', cursor: 'pointer' }}>Cancel</button>
          <button type="submit" disabled={createMut.isPending || updateMut.isPending}
            className="rounded-lg border-none px-6 py-2.5 text-[14px] font-semibold text-white disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', cursor: 'pointer' }}>
            {(createMut.isPending || updateMut.isPending) ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Resource')}
          </button>
        </div>
      </form>
    </div>
  )
}
