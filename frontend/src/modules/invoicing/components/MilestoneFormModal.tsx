// See FSD §2.8 — Milestone create/edit modal
import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { createMilestone, updateMilestone, type Milestone, type MilestoneCreatePayload } from '../api'

interface MilestoneFormModalProps {
  open: boolean
  projectId: string
  editingMilestone: Milestone | null
  onClose: () => void
}

interface FormErrors {
  name?: string
  amount?: string
  planned_delivery_date?: string
}

export function MilestoneFormModal({ open, projectId, editingMilestone, onClose }: MilestoneFormModalProps) {
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [plannedDate, setPlannedDate] = useState('')
  const [sortOrder, setSortOrder] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})

  useEffect(() => {
    if (!open) return
    if (editingMilestone) {
      setName(editingMilestone.name)
      setAmount(String(editingMilestone.amount ?? ''))
      setPlannedDate(editingMilestone.planned_delivery_date ?? '')
      setSortOrder(editingMilestone.sort_order != null ? String(editingMilestone.sort_order) : '')
    } else {
      setName('')
      setAmount('')
      setPlannedDate('')
      setSortOrder('')
    }
    setErrors({})
  }, [open, editingMilestone])

  const amountNum = parseFloat(amount) || 0

  function validate(): boolean {
    const e: FormErrors = {}
    if (!name.trim()) e.name = 'Milestone name is required'
    if (!amount || amountNum <= 0) e.amount = 'Milestone amount must be positive'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const saveMutation = useMutation({
    mutationFn: (payload: MilestoneCreatePayload) =>
      editingMilestone
        ? updateMilestone(projectId, editingMilestone.id, payload)
        : createMilestone(projectId, payload),
    onSuccess: () => {
      toast.success(editingMilestone ? 'Milestone updated' : 'Milestone created')
      queryClient.invalidateQueries({ queryKey: ['project-milestones', projectId] })
      onClose()
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || 'Failed to save milestone'
      toast.error(msg)
    },
  })

  function handleSave() {
    if (!validate()) return
    const payload: MilestoneCreatePayload = {
      name: name.trim(),
      amount: amountNum,
      planned_delivery_date: plannedDate || null,
      sort_order: sortOrder ? parseInt(sortOrder, 10) : null,
    }
    saveMutation.mutate(payload)
  }

  if (!open) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(27,43,101,0.5)',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backdropFilter: 'blur(2px)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          width: 480,
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px 16px',
            borderBottom: '1px solid #E8EAF6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1e1b4b' }}>
            {editingMilestone ? 'Edit Milestone' : 'Add Milestone'}
          </h2>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#7C85C0', padding: 4, borderRadius: 6 }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 24px' }}>
          {/* Name */}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              Name <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Requirements & Design Sign-off"
              style={{
                width: '100%', padding: '10px 14px', border: `1px solid ${errors.name ? '#ef4444' : '#D6DAF0'}`,
                borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
              }}
            />
            {errors.name && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.name}</div>}
          </div>

          {/* Amount + Sort Order (2-col) */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 18 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
                Amount <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                min="0.01"
                style={{
                  width: '100%', padding: '10px 14px', border: `1px solid ${errors.amount ? '#ef4444' : '#D6DAF0'}`,
                  borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
                }}
              />
              {errors.amount && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.amount}</div>}
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
                Sort Order
              </label>
              <input
                type="number"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                placeholder="1"
                min="1"
                step="1"
                style={{
                  width: '100%', padding: '10px 14px', border: '1px solid #D6DAF0',
                  borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
                }}
              />
            </div>
          </div>

          {/* Planned Delivery Date */}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              Planned Delivery Date
            </label>
            <input
              type="date"
              value={plannedDate}
              onChange={(e) => setPlannedDate(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: '1px solid #D6DAF0',
                borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 24px 20px',
            borderTop: '1px solid #E8EAF6',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 10,
          }}
        >
          <button
            onClick={onClose}
            style={{
              padding: '10px 20px', border: '1px solid #D6DAF0', borderRadius: 8,
              fontSize: 14, cursor: 'pointer', background: '#fff', color: '#1e1b4b',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            style={{
              padding: '10px 24px', border: 'none', borderRadius: 8,
              fontSize: 14, fontWeight: 600, cursor: saveMutation.isPending ? 'not-allowed' : 'pointer',
              background: '#FF4B2B', color: '#fff', opacity: saveMutation.isPending ? 0.7 : 1,
            }}
          >
            {saveMutation.isPending ? 'Saving...' : editingMilestone ? 'Update Milestone' : 'Add Milestone'}
          </button>
        </div>
      </div>
    </div>
  )
}
