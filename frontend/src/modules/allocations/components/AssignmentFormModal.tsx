import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { X, AlertTriangle } from 'lucide-react'
import { useAuthStore } from '../../auth/store'
import { createAssignment, updateAssignment } from '../api'
import type { AssignmentCreatePayload, AssignmentUpdatePayload, AssignmentListItem } from '../api'
import { fetchResources } from '../../resources/api'
import type { ResourceListItem } from '../../resources/api'

interface AssignmentFormModalProps {
  open: boolean
  projectId: string
  projectName: string
  editingAssignment?: AssignmentListItem | null
  onClose: () => void
}

interface FormState {
  resource_id: string
  allocation_pct: string
  billability_pct: string
  is_shadow: boolean
  start_date: string
  end_date: string
  project_designation: string
  project_expertise: string
}

const INITIAL_FORM: FormState = {
  resource_id: '',
  allocation_pct: '',
  billability_pct: '0',
  is_shadow: false,
  start_date: '',
  end_date: '',
  project_designation: '',
  project_expertise: '',
}

export function AssignmentFormModal({ open, projectId, projectName, editingAssignment, onClose }: AssignmentFormModalProps) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canSeeCost = user && ['CEO', 'CTO', 'FINANCE'].includes(user.role.code)
  const isEditing = !!editingAssignment
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [overAllocWarning, setOverAllocWarning] = useState<string | null>(null)

  const { data: resourcesData } = useQuery({
    queryKey: ['resources-dropdown-alloc'],
    queryFn: () => fetchResources({ limit: 100, status: 'ACTIVE' }),
    enabled: open,
  })

  const resources: ResourceListItem[] = resourcesData?.data ?? []

  useEffect(() => {
    if (!open) return
    if (editingAssignment) {
      setForm({
        resource_id: editingAssignment.resource?.id ?? '',
        allocation_pct: String(editingAssignment.allocation_pct),
        billability_pct: editingAssignment.billability_pct !== null ? String(editingAssignment.billability_pct) : '0',
        is_shadow: editingAssignment.is_shadow ?? false,
        start_date: editingAssignment.start_date ?? '',
        end_date: editingAssignment.end_date ?? '',
        project_designation: editingAssignment.project_designation ?? '',
        project_expertise: editingAssignment.project_expertise ?? '',
      })
    } else {
      setForm(INITIAL_FORM)
    }
    setErrors({})
    setServerError(null)
    setOverAllocWarning(null)
  }, [open, editingAssignment])

  const selectedResource = useMemo(
    () => resources.find((r) => r.id === form.resource_id),
    [resources, form.resource_id],
  )

  useEffect(() => {
    if (!selectedResource) {
      setOverAllocWarning(null)
      return
    }
    const alloc = parseInt(form.allocation_pct) || 0
    const existingAlloc = isEditing ? editingAssignment!.allocation_pct : 0
    const total = selectedResource.total_allocation_pct - existingAlloc + alloc
    if (total > 100) {
      setOverAllocWarning(
        `This will bring total allocation for ${selectedResource.name} to ${total}% (currently ${selectedResource.total_allocation_pct - existingAlloc}% across other projects)`,
      )
    } else {
      setOverAllocWarning(null)
    }
  }, [form.resource_id, form.allocation_pct, selectedResource, isEditing, editingAssignment])

  function validate(): boolean {
    const errs: Record<string, string> = {}
    if (!form.resource_id) errs.resource_id = 'Resource is required'
    const alloc = parseInt(form.allocation_pct)
    if (!form.allocation_pct || isNaN(alloc) || alloc < 1 || alloc > 100) {
      errs.allocation_pct = 'Allocation must be between 1% and 100%'
    }
    const bill = parseInt(form.billability_pct)
    if (form.billability_pct === '' || isNaN(bill) || bill < 0 || bill > 100) {
      errs.billability_pct = 'Billability must be between 0% and 100%'
    } else if (!form.is_shadow && bill > alloc) {
      errs.billability_pct = 'Billability cannot exceed allocation percentage'
    }
    if (form.is_shadow && bill !== 0) {
      errs.billability_pct = 'Shadow resources cannot have billability'
    }
    if (!form.start_date) errs.start_date = 'Start date is required'
    if (form.start_date && form.end_date && form.end_date <= form.start_date) {
      errs.end_date = 'End date must be after start date'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const createMut = useMutation({
    mutationFn: (payload: AssignmentCreatePayload) => createAssignment(projectId, payload),
    onSuccess: (resp) => {
      if (resp.warnings?.length) {
        resp.warnings.forEach((w) => toast.warning(w))
      }
      toast.success('Assignment created')
      queryClient.invalidateQueries({ queryKey: ['project-assignments', projectId] })
      onClose()
    },
    onError: (err: any) => {
      setServerError(err.response?.data?.message || 'Failed to create assignment')
    },
  })

  const updateMut = useMutation({
    mutationFn: (payload: AssignmentUpdatePayload) => updateAssignment(editingAssignment!.id, payload),
    onSuccess: (resp) => {
      if (resp.warnings?.length) {
        resp.warnings.forEach((w) => toast.warning(w))
      }
      toast.success('Assignment updated')
      queryClient.invalidateQueries({ queryKey: ['project-assignments', projectId] })
      onClose()
    },
    onError: (err: any) => {
      setServerError(err.response?.data?.message || 'Failed to update assignment')
    },
  })

  function handleSubmit() {
    setServerError(null)
    if (!validate()) return

    const alloc = parseInt(form.allocation_pct)
    const bill = parseInt(form.billability_pct)

    if (isEditing) {
      const payload: AssignmentUpdatePayload = {
        allocation_pct: alloc,
        billability_pct: bill,
        is_shadow: form.is_shadow,
        start_date: form.start_date,
        end_date: form.end_date || null,
        project_designation: form.project_designation || null,
        project_expertise: form.project_expertise || null,
      }
      updateMut.mutate(payload)
    } else {
      const payload: AssignmentCreatePayload = {
        resource_id: form.resource_id,
        allocation_pct: alloc,
        billability_pct: bill,
        is_shadow: form.is_shadow,
        start_date: form.start_date,
        end_date: form.end_date || null,
        project_designation: form.project_designation || null,
        project_expertise: form.project_expertise || null,
      }
      createMut.mutate(payload)
    }
  }

  function handleShadowToggle(checked: boolean) {
    setForm((f) => ({
      ...f,
      is_shadow: checked,
      billability_pct: checked ? '0' : f.billability_pct,
    }))
    if (checked) {
      setErrors((e) => {
        const next = { ...e }
        delete next.billability_pct
        return next
      })
    }
  }

  if (!open) return null

  const isSaving = createMut.isPending || updateMut.isPending

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(2px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="my-8 w-full max-w-[580px] rounded-xl"
        style={{ background: '#F0F1FA' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-0">
          <div>
            <h2 className="text-[20px] font-bold" style={{ color: '#1e1b4b' }}>
              {isEditing ? 'Edit Assignment' : 'Add Assignment'}
            </h2>
            <p className="text-[13px]" style={{ color: '#6b7280' }}>Project: {projectName}</p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-[18px]"
            style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-6 py-4">
          {/* Server Error */}
          {serverError && (
            <div
              className="mb-4 flex items-center gap-2 rounded-lg px-4 py-2.5 text-[12px] font-medium"
              style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }}
            >
              <AlertTriangle size={16} />
              {serverError}
            </div>
          )}

          {/* Over-allocation Warning */}
          {overAllocWarning && (
            <div
              className="mb-4 flex items-center gap-2 rounded-lg px-4 py-2.5 text-[12px] font-medium"
              style={{ background: '#fef3c7', border: '1px solid #fde68a', color: '#92400e' }}
            >
              <AlertTriangle size={16} />
              {overAllocWarning}
            </div>
          )}

          {/* Assignment Details Card */}
          <div
            className="mb-4 rounded-xl p-6"
            style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}
          >
            <div
              className="mb-4 pb-2 text-[13px] font-bold uppercase tracking-wide"
              style={{ color: '#2B3990', borderBottom: '2px solid #E8EAF6' }}
            >
              Assignment Details
            </div>

            {/* Resource Selector */}
            <div className="mb-3.5">
              <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                Resource <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                value={form.resource_id}
                onChange={(e) => setForm((f) => ({ ...f, resource_id: e.target.value }))}
                disabled={isEditing}
                className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                style={{
                  border: `1px solid ${errors.resource_id ? '#ef4444' : '#D6DAF0'}`,
                  background: isEditing ? '#F5F6FC' : '#fff',
                  color: isEditing ? '#7C85C0' : '#1e1b4b',
                }}
              >
                <option value="">Select a resource...</option>
                {resources.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.employee_id}) — {r.designation}
                  </option>
                ))}
              </select>
              {errors.resource_id && (
                <div className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.resource_id}</div>
              )}
              {selectedResource && (
                <div
                  className="mt-1.5 flex flex-col gap-1.5 rounded-lg px-3 py-2 text-[12px]"
                  style={{ background: '#F5F6FC', color: '#6b7280' }}
                >
                  <div className="flex items-center gap-2">
                    Current allocation: <strong>{selectedResource.total_allocation_pct}%</strong> across projects
                    <span
                      className="rounded-xl px-2 py-0.5 text-[11px] font-semibold"
                      style={{
                        background: selectedResource.total_allocation_pct >= 80 ? '#fef3c7' : '#dcfce7',
                        color: selectedResource.total_allocation_pct >= 80 ? '#92400e' : '#15803d',
                      }}
                    >
                      {selectedResource.total_allocation_pct}% allocated
                    </span>
                  </div>
                  {canSeeCost && selectedResource.loaded_cost_monthly && (
                    <div className="flex items-center gap-1">
                      Loaded cost: <strong style={{ color: '#2B3990' }}>₹{selectedResource.loaded_cost_monthly.toLocaleString('en-IN')}</strong>/month
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Allocation & Billability */}
            <div className="mb-3.5 grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  Allocation % <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={form.allocation_pct}
                  onChange={(e) => setForm((f) => ({ ...f, allocation_pct: e.target.value }))}
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{ border: `1px solid ${errors.allocation_pct ? '#ef4444' : '#D6DAF0'}`, background: errors.allocation_pct ? '#fef2f2' : '#fff' }}
                  placeholder="e.g. 50"
                />
                <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>Capacity consumed (1-100%)</div>
                {errors.allocation_pct && (
                  <div className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.allocation_pct}</div>
                )}
              </div>
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  Billability % <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={form.billability_pct}
                  onChange={(e) => setForm((f) => ({ ...f, billability_pct: e.target.value }))}
                  disabled={form.is_shadow}
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{
                    border: `1px solid ${errors.billability_pct ? '#ef4444' : '#D6DAF0'}`,
                    background: form.is_shadow ? '#F5F6FC' : errors.billability_pct ? '#fef2f2' : '#fff',
                    color: form.is_shadow ? '#7C85C0' : '#1e1b4b',
                  }}
                />
                {errors.billability_pct && (
                  <div className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.billability_pct}</div>
                )}
              </div>
            </div>

            {/* Shadow Toggle */}
            <div className="mb-1 flex items-center gap-2 py-2">
              <input
                type="checkbox"
                checked={form.is_shadow}
                onChange={(e) => handleShadowToggle(e.target.checked)}
                className="h-[18px] w-[18px]"
                style={{ accentColor: '#2B3990', cursor: 'pointer' }}
              />
              <div>
                <div className="text-[13px] font-medium" style={{ color: '#1e1b4b' }}>Shadow Assignment</div>
                <div className="text-[11px]" style={{ color: '#7C85C0' }}>Shadow resources have 0% billability and no billing rate</div>
              </div>
            </div>
          </div>

          {/* Dates & Overrides Card */}
          <div
            className="mb-4 rounded-xl p-6"
            style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}
          >
            <div
              className="mb-4 pb-2 text-[13px] font-bold uppercase tracking-wide"
              style={{ color: '#2B3990', borderBottom: '2px solid #E8EAF6' }}
            >
              Dates & Overrides
            </div>

            <div className="mb-3.5 grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  Start Date <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{ border: `1px solid ${errors.start_date ? '#ef4444' : '#D6DAF0'}` }}
                />
                {errors.start_date && (
                  <div className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.start_date}</div>
                )}
              </div>
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  End Date
                </label>
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{ border: `1px solid ${errors.end_date ? '#ef4444' : '#D6DAF0'}` }}
                />
                <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>Leave empty for ongoing assignment</div>
                {errors.end_date && (
                  <div className="mt-1 text-[12px]" style={{ color: '#ef4444' }}>{errors.end_date}</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  Project Designation Override
                </label>
                <input
                  type="text"
                  value={form.project_designation}
                  onChange={(e) => setForm((f) => ({ ...f, project_designation: e.target.value }))}
                  placeholder="e.g. Frontend Lead"
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{ border: '1px solid #D6DAF0' }}
                />
                <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>Overrides resource's default designation for this project</div>
              </div>
              <div>
                <label className="mb-1.5 block text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
                  Project Expertise Override
                </label>
                <input
                  type="text"
                  value={form.project_expertise}
                  onChange={(e) => setForm((f) => ({ ...f, project_expertise: e.target.value }))}
                  placeholder="e.g. React, GraphQL"
                  className="w-full rounded-lg px-3 py-2.5 text-[13px]"
                  style={{ border: '1px solid #D6DAF0' }}
                />
                <div className="mt-1 text-[11px]" style={{ color: '#7C85C0' }}>Overrides resource's default expertise for this project</div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2.5 pt-2">
            <button
              onClick={onClose}
              className="rounded-lg px-7 py-2.5 text-[14px] font-medium"
              style={{ background: '#fff', color: '#6b7280', border: '1px solid #D6DAF0', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSaving}
              className="rounded-lg border-none px-7 py-2.5 text-[14px] font-semibold text-white"
              style={{ background: '#FF4B2B', cursor: isSaving ? 'not-allowed' : 'pointer', opacity: isSaving ? 0.7 : 1 }}
            >
              {isSaving ? 'Saving...' : 'Save Assignment'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
