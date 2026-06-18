import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { useAuthStore } from '../../auth/store'
import { createProject, fetchProject, updateProject, type ProjectCreatePayload } from '../api'
import { fetchClients } from '../../clients/api'
import { fetchResourcesDropdown } from '../../resources/api'
import { Breadcrumb, SearchableSelect } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'

const inputStyle = {
  border: '1px solid #D6DAF0',
  background: '#F0F1FA',
  color: '#1e1b4b',
}

const focusHandlers = {
  onFocus: (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.target.style.borderColor = '#4A5BB5'
    e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'
    e.target.style.background = '#fff'
  },
  onBlur: (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.target.style.borderColor = '#D6DAF0'
    e.target.style.boxShadow = 'none'
    e.target.style.background = '#F0F1FA'
  },
}

export function ProjectForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const isDM = user?.role.code === 'DM'

  const [name, setName] = useState('')
  const [clientId, setClientId] = useState('')
  const [type, setType] = useState('FIXED_PRICE')
  const [billingCurrency, setBillingCurrency] = useState('INR')
  const [startDate, setStartDate] = useState('')
  const [contractEndDate, setContractEndDate] = useState('')
  const [dmId, setDmId] = useState('')
  const [pmId, setPmId] = useState('')
  const [worklogEnabled, setWorklogEnabled] = useState(false)
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  useDocumentTitle(isEdit ? 'Edit Project' : 'New Project')

  const { data: existingProject } = useQuery({
    queryKey: ['project', id],
    queryFn: () => fetchProject(id!),
    enabled: isEdit,
  })

  const { data: clientsData } = useQuery({
    queryKey: ['clients-dropdown'],
    queryFn: () => fetchClients({ limit: 100, status: 'ACTIVE' }),
  })

  const { data: resources } = useQuery({
    queryKey: ['resources-dropdown'],
    queryFn: fetchResourcesDropdown,
  })

  useEffect(() => {
    if (isEdit && existingProject?.data) {
      const p = existingProject.data
      setName(p.name)
      setClientId(p.client.id)
      setType(p.type)
      setBillingCurrency(p.billing_currency)
      setStartDate(p.start_date ?? '')
      setContractEndDate(p.contract_end_date ?? '')
      setDmId(p.dm.id)
      setPmId(p.pm.id)
      setWorklogEnabled(p.worklog_enabled)
      setNotes(p.notes ?? '')
    }
  }, [isEdit, existingProject])

  useEffect(() => {
    if (!isEdit && isDM && user?.resource_id) {
      setDmId(user.resource_id)
    }
  }, [isEdit, isDM, user])

  const contractEndRequired = type === 'TIME_AND_MATERIAL' || type === 'CLIENT_ONBOARDING'

  function validate(): boolean {
    const e: Record<string, string> = {}
    if (!name.trim()) e.name = 'Project name is required'
    if (!clientId) e.clientId = 'Client is required'
    if (!dmId) e.dmId = 'Delivery Manager is required'
    if (!pmId) e.pmId = 'Project Manager is required'
    if (contractEndRequired && !contractEndDate) {
      e.contractEndDate = 'Contract end date is required for T&M and Onboarding projects'
    }
    if (startDate && contractEndDate && contractEndDate <= startDate) {
      e.contractEndDate = 'Contract end date must be after start date'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const saveMut = useMutation({
    mutationFn: (payload: ProjectCreatePayload) =>
      isEdit ? updateProject(id!, payload) : createProject(payload),
    onSuccess: (data) => {
      toast.success(isEdit ? 'Project updated' : 'Project created')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      navigate(`/projects/${data.data.id}`)
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || 'Failed to save project'
      const field = err.response?.data?.field
      if (field) {
        setErrors((prev) => ({ ...prev, [field]: msg }))
      } else {
        toast.error(msg)
      }
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    saveMut.mutate({
      name: name.trim(),
      client_id: clientId,
      type,
      billing_currency: billingCurrency,
      start_date: startDate || null,
      contract_end_date: contractEndDate || null,
      dm_id: dmId,
      pm_id: pmId,
      worklog_enabled: worklogEnabled,
      notes: notes.trim() || null,
    })
  }

  const clients = clientsData?.data ?? []
  const resourceList = resources ?? []

  const breadcrumbItems = isEdit
    ? [{ label: 'Projects', to: '/projects' }, { label: existingProject?.data?.name ?? '...', to: `/projects/${id}` }, { label: 'Edit' }]
    : [{ label: 'Projects', to: '/projects' }, { label: 'New Project' }]

  return (
    <div>
      <Breadcrumb items={breadcrumbItems} />

      <div className="mb-5">
        <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>
          {isEdit ? 'Edit Project' : 'Create New Project'}
        </h1>
        <p className="mt-0.5 text-[13px]" style={{ color: '#6b7280' }}>
          {isEdit ? 'Update project details' : 'Fill in the details to create a new project'}
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div
          className="rounded-xl p-6"
          style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
        >
          <div className="grid gap-5" style={{ gridTemplateColumns: '1fr 1fr' }}>
            {/* Name */}
            <div className="col-span-2">
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Project Name <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter project name"
                className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none transition-all"
                style={inputStyle}
                {...focusHandlers}
              />
              {errors.name && <p className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.name}</p>}
            </div>

            {/* Client */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Client <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <SearchableSelect
                value={clientId}
                onChange={setClientId}
                options={[
                  { value: '', label: 'Select client' },
                  ...clients.map((c) => ({ value: c.id, label: c.name })),
                ]}
                placeholder="Select client"
                error={!!errors.clientId}
              />
              {errors.clientId && <p className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.clientId}</p>}
            </div>

            {/* Billing Currency */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Billing Currency
              </label>
              <SearchableSelect
                value={billingCurrency}
                onChange={setBillingCurrency}
                options={[
                  { value: 'INR', label: 'INR' },
                  { value: 'USD', label: 'USD' },
                  { value: 'EUR', label: 'EUR' },
                  { value: 'GBP', label: 'GBP' },
                  { value: 'AED', label: 'AED' },
                  { value: 'SGD', label: 'SGD' },
                  { value: 'AUD', label: 'AUD' },
                  { value: 'CAD', label: 'CAD' },
                ]}
                placeholder="Select currency"
              />
            </div>

            {/* Type — radio buttons */}
            <div className="col-span-2">
              <label className="mb-2 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Project Type <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <div className="flex gap-4">
                {[
                  { value: 'FIXED_PRICE', label: 'Fixed Price' },
                  { value: 'TIME_AND_MATERIAL', label: 'Time & Material' },
                  { value: 'CLIENT_ONBOARDING', label: 'Client Onboarding' },
                ].map((opt) => (
                  <label
                    key={opt.value}
                    className="flex cursor-pointer items-center gap-2 rounded-lg px-4 py-2.5 text-[13.5px] font-medium transition-all"
                    style={{
                      border: `2px solid ${type === opt.value ? '#2B3990' : '#D6DAF0'}`,
                      background: type === opt.value ? 'rgba(43,57,144,0.04)' : '#fff',
                      color: type === opt.value ? '#2B3990' : '#6b7280',
                    }}
                  >
                    <input
                      type="radio"
                      name="type"
                      value={opt.value}
                      checked={type === opt.value}
                      onChange={(e) => setType(e.target.value)}
                      className="hidden"
                    />
                    <div
                      className="flex h-4 w-4 items-center justify-center rounded-full"
                      style={{ border: `2px solid ${type === opt.value ? '#2B3990' : '#D6DAF0'}` }}
                    >
                      {type === opt.value && (
                        <div className="h-2 w-2 rounded-full" style={{ background: '#2B3990' }} />
                      )}
                    </div>
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Start Date */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none transition-all"
                style={inputStyle}
                {...focusHandlers}
              />
            </div>

            {/* Contract End Date */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Contract End Date {contractEndRequired && <span style={{ color: '#ef4444' }}>*</span>}
              </label>
              <input
                type="date"
                value={contractEndDate}
                onChange={(e) => setContractEndDate(e.target.value)}
                className="w-full rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none transition-all"
                style={inputStyle}
                {...focusHandlers}
              />
              {errors.contractEndDate && <p className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.contractEndDate}</p>}
            </div>

            {/* DM */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Delivery Manager <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <SearchableSelect
                value={dmId}
                onChange={setDmId}
                options={[
                  { value: '', label: 'Select DM' },
                  ...resourceList.map((r) => ({ value: r.id, label: r.name })),
                ]}
                placeholder="Select DM"
                disabled={isDM && !isEdit}
                error={!!errors.dmId}
              />
              {errors.dmId && <p className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.dmId}</p>}
            </div>

            {/* PM */}
            <div>
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Project Manager <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <SearchableSelect
                value={pmId}
                onChange={setPmId}
                options={[
                  { value: '', label: 'Select PM' },
                  ...resourceList.map((r) => ({ value: r.id, label: r.name })),
                ]}
                placeholder="Select PM"
                error={!!errors.pmId}
              />
              {errors.pmId && <p className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.pmId}</p>}
            </div>

            {/* Worklog Enabled */}
            <div className="col-span-2">
              <label className="flex cursor-pointer items-center gap-3">
                <div
                  className="relative h-6 w-11 rounded-full transition-colors"
                  style={{ background: worklogEnabled ? '#2B3990' : '#D6DAF0' }}
                  onClick={() => setWorklogEnabled(!worklogEnabled)}
                >
                  <div
                    className="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform"
                    style={{
                      left: worklogEnabled ? '22px' : '2px',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
                    }}
                  />
                </div>
                <span className="text-[13.5px] font-medium" style={{ color: '#1e1b4b' }}>
                  Enable Worklogs
                </span>
              </label>
            </div>

            {/* Notes */}
            <div className="col-span-2">
              <label className="mb-1.5 block text-[13px] font-semibold" style={{ color: '#1e1b4b' }}>
                Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Optional notes about this project"
                className="w-full resize-none rounded-lg px-3.5 py-[9px] text-[13.5px] outline-none transition-all"
                style={inputStyle}
                onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'; e.target.style.background = '#fff' }}
                onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.boxShadow = 'none'; e.target.style.background = '#F0F1FA' }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 flex justify-end gap-3" style={{ borderTop: '1px solid #E8EAF6', paddingTop: '20px' }}>
            <button
              type="button"
              onClick={() => navigate('/projects')}
              className="rounded-lg px-5 py-2.5 text-[14px] font-medium transition-colors"
              style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveMut.isPending}
              className="rounded-lg border-none px-6 py-2.5 text-[14px] font-semibold text-white transition-all disabled:opacity-60"
              style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}
            >
              {saveMut.isPending ? 'Saving...' : isEdit ? 'Update Project' : 'Create Project'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
