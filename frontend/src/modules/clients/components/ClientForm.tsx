import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { createClient, fetchClient, updateClient } from '../api'

export function ClientForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [form, setForm] = useState({
    name: '',
    industry: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    engagement_start_date: '',
    notes: '',
  })
  const [error, setError] = useState<{ message: string; field?: string } | null>(null)

  const { data: clientData } = useQuery({
    queryKey: ['client', id],
    queryFn: () => fetchClient(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (isEdit && clientData?.data) {
      const c = clientData.data
      setForm({
        name: c.name,
        industry: c.industry || '',
        contact_name: c.contact_name || '',
        contact_email: c.contact_email || '',
        contact_phone: c.contact_phone || '',
        engagement_start_date: c.engagement_start_date || '',
        notes: c.notes || '',
      })
    }
  }, [isEdit, clientData])

  const createMut = useMutation({
    mutationFn: () => createClient({
      name: form.name,
      industry: form.industry || undefined,
      contact_name: form.contact_name || undefined,
      contact_email: form.contact_email || undefined,
      contact_phone: form.contact_phone || undefined,
      engagement_start_date: form.engagement_start_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: (data) => {
      toast.success('Client created')
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      navigate(`/clients/${data.data.id}`)
    },
    onError: (e: any) => {
      setError({ message: e.response?.data?.message || 'Failed to create', field: e.response?.data?.field })
    },
  })

  const updateMut = useMutation({
    mutationFn: () => updateClient(id!, {
      name: form.name,
      industry: form.industry || undefined,
      contact_name: form.contact_name || undefined,
      contact_email: form.contact_email || undefined,
      contact_phone: form.contact_phone || undefined,
      engagement_start_date: form.engagement_start_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => {
      toast.success('Client updated')
      queryClient.invalidateQueries({ queryKey: ['client', id] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      navigate(`/clients/${id}`)
    },
    onError: (e: any) => {
      setError({ message: e.response?.data?.message || 'Failed to update', field: e.response?.data?.field })
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!form.name) {
      setError({ message: 'Client name is required', field: 'name' })
      return
    }
    if (form.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email)) {
      setError({ message: 'Invalid email format', field: 'contact_email' })
      return
    }
    isEdit ? updateMut.mutate() : createMut.mutate()
  }

  const inputStyle = { border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA' }
  const labelStyle = { color: '#1e1b4b', fontSize: '13.5px', fontWeight: 600 as const, marginBottom: '4px', display: 'block' as const }

  return (
    <div>
      <div className="mb-1 text-[13px]" style={{ color: '#7C85C0' }}>
        <span className="cursor-pointer hover:underline" onClick={() => navigate('/clients')}>Clients</span>
        <span style={{ color: '#6b7280' }}> &rsaquo; </span>
        <span style={{ color: '#6b7280' }}>{isEdit ? 'Edit Client' : 'Add Client'}</span>
      </div>

      <h1 className="mb-5 text-[22px] font-bold" style={{ color: '#1e1b4b' }}>{isEdit ? 'Edit Client' : 'Add Client'}</h1>

      <form onSubmit={handleSubmit} className="mx-auto max-w-[640px] rounded-xl p-6" style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}>
        {error && (
          <div className="mb-4 rounded-lg px-4 py-3 text-[13.5px] font-medium" style={{ background: '#fef2f2', color: '#ef4444', border: '1px solid #fecaca' }}>
            {error.message}
          </div>
        )}

        <div className="mb-4">
          <label htmlFor="client-name" style={labelStyle}>Client Name <span style={{ color: '#ef4444' }}>*</span></label>
          <input id="client-name" type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={{ ...inputStyle, borderColor: error?.field === 'name' ? '#ef4444' : '#D6DAF0' }}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = error?.field === 'name' ? '#ef4444' : '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
        </div>

        <div className="mb-4">
          <label style={labelStyle}>Industry</label>
          <input type="text" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })}
            className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
        </div>

        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label style={labelStyle}>Contact Name</label>
            <input type="text" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
          <div>
            <label style={labelStyle}>Contact Email</label>
            <input type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={{ ...inputStyle, borderColor: error?.field === 'contact_email' ? '#ef4444' : '#D6DAF0' }}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = error?.field === 'contact_email' ? '#ef4444' : '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label style={labelStyle}>Contact Phone</label>
            <input type="text" value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
          <div>
            <label style={labelStyle}>Engagement Start Date</label>
            <input type="date" value={form.engagement_start_date} onChange={(e) => setForm({ ...form, engagement_start_date: e.target.value })}
              className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
              onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
              onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
          </div>
        </div>

        <div className="mb-5">
          <label style={labelStyle}>Notes</label>
          <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3}
            className="w-full resize-none rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none" style={inputStyle}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.background = '#F0F1FA' }} />
        </div>

        <div className="flex justify-end gap-3 pt-2" style={{ borderTop: '1px solid #E8EAF6' }}>
          <button type="button" onClick={() => navigate(isEdit ? `/clients/${id}` : '/clients')}
            className="rounded-lg px-6 py-2.5 text-[13.5px] font-medium" style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280', cursor: 'pointer' }}>Cancel</button>
          <button type="submit" disabled={createMut.isPending || updateMut.isPending}
            className="rounded-lg border-none px-6 py-2.5 text-[14px] font-semibold text-white disabled:opacity-50" style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', cursor: 'pointer' }}>
            {(createMut.isPending || updateMut.isPending) ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Client')}
          </button>
        </div>
      </form>
    </div>
  )
}
