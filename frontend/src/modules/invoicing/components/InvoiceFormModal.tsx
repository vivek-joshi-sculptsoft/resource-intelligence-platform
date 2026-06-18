// See FSD §2.9, §11 — Invoice create/edit modal
import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { createInvoice, updateInvoice, fetchMilestones, type Invoice, type InvoiceCreatePayload } from '../api'

interface InvoiceFormModalProps {
  open: boolean
  projectId: string
  projectType: string
  billingCurrency: string
  editingInvoice: Invoice | null
  onClose: () => void
}

interface FormErrors {
  amount?: string
  exchange_rate?: string
  milestone_id?: string
}

function formatInr(val: number): string {
  if (!val || val <= 0) return '—'
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

export function InvoiceFormModal({ open, projectId, projectType, billingCurrency, editingInvoice, onClose }: InvoiceFormModalProps) {
  const queryClient = useQueryClient()
  const isFP = projectType === 'FIXED_PRICE'
  const isInr = billingCurrency.toUpperCase() === 'INR'

  const [invoiceDate, setInvoiceDate] = useState('')
  const [amount, setAmount] = useState('')
  const [exchangeRate, setExchangeRate] = useState('')
  const [milestoneId, setMilestoneId] = useState('')
  const [billingStart, setBillingStart] = useState('')
  const [billingEnd, setBillingEnd] = useState('')
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})

  const { data: milestonesData } = useQuery({
    queryKey: ['project-milestones', projectId],
    queryFn: () => fetchMilestones(projectId),
    enabled: open && isFP,
  })

  const milestoneOptions = useMemo(() => {
    const all = milestonesData?.data ?? []
    const approved = all.filter((m) => m.status === 'APPROVED')
    if (editingInvoice?.milestone && !approved.some((m) => m.id === editingInvoice.milestone!.id)) {
      return [editingInvoice.milestone, ...approved]
    }
    return approved
  }, [milestonesData, editingInvoice])

  useEffect(() => {
    if (!open) return
    if (editingInvoice) {
      setInvoiceDate(editingInvoice.invoice_date ?? '')
      setAmount(String(editingInvoice.amount ?? ''))
      setExchangeRate(String(editingInvoice.exchange_rate ?? ''))
      setMilestoneId(editingInvoice.milestone_id ?? '')
      setBillingStart(editingInvoice.billing_period_start ?? '')
      setBillingEnd(editingInvoice.billing_period_end ?? '')
      setNotes(editingInvoice.notes ?? '')
    } else {
      setInvoiceDate('')
      setAmount('')
      setExchangeRate(isInr ? '1' : '')
      setMilestoneId('')
      setBillingStart('')
      setBillingEnd('')
      setNotes('')
    }
    setErrors({})
  }, [open, editingInvoice, isInr])

  const amountNum = parseFloat(amount) || 0
  const exchangeRateNum = isInr ? 1 : parseFloat(exchangeRate) || 0
  const amountInr = amountNum * exchangeRateNum

  function validate(): boolean {
    const e: FormErrors = {}
    if (!amount || amountNum <= 0) e.amount = 'Invoice amount must be positive'
    if (!isInr && (!exchangeRate || exchangeRateNum <= 0)) e.exchange_rate = 'Exchange rate must be positive'
    if (isFP && !milestoneId) e.milestone_id = 'Fixed price invoices must be linked to a milestone'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const saveMutation = useMutation({
    mutationFn: (payload: InvoiceCreatePayload) =>
      editingInvoice
        ? updateInvoice(projectId, editingInvoice.id, payload)
        : createInvoice(projectId, payload),
    onSuccess: () => {
      toast.success(editingInvoice ? 'Invoice updated' : 'Invoice created')
      queryClient.invalidateQueries({ queryKey: ['project-invoices', projectId] })
      onClose()
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || 'Failed to save invoice'
      toast.error(msg)
    },
  })

  function handleSave() {
    if (!validate()) return
    const payload: InvoiceCreatePayload = {
      invoice_date: invoiceDate,
      amount: amountNum,
      currency: billingCurrency,
      exchange_rate: isInr ? 1 : exchangeRateNum,
      milestone_id: isFP ? milestoneId : null,
      billing_period_start: !isFP ? (billingStart || null) : null,
      billing_period_end: !isFP ? (billingEnd || null) : null,
      notes: notes.trim() || null,
    }
    saveMutation.mutate(payload)
  }

  if (!open) return null

  const inputStyle = (hasError: boolean) => ({
    width: '100%', padding: '10px 14px', border: `1px solid ${hasError ? '#ef4444' : '#D6DAF0'}`,
    borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
  })

  const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 } as const

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(27,43,101,0.5)', zIndex: 2000,
        display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(2px)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{ background: '#fff', borderRadius: 16, boxShadow: '0 20px 60px rgba(0,0,0,0.2)', width: 560, maxHeight: '90vh', overflowY: 'auto' }}>
        {/* Header */}
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #E8EAF6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1e1b4b' }}>
            {editingInvoice ? 'Edit Invoice' : 'Create Invoice'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#7C85C0', padding: 4, borderRadius: 6 }}>
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 24px' }}>
          {/* Milestone (FP only) */}
          {isFP && (
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>
                Milestone <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                value={milestoneId}
                onChange={(e) => setMilestoneId(e.target.value)}
                style={inputStyle(!!errors.milestone_id)}
              >
                <option value="">Select an approved milestone...</option>
                {milestoneOptions.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.amount != null ? `(${formatInr(m.amount)})` : ''}
                  </option>
                ))}
              </select>
              <div style={{ fontSize: 12, color: '#7C85C0', marginTop: 4 }}>
                Only milestones with APPROVED status are available for invoicing
              </div>
              {errors.milestone_id && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.milestone_id}</div>}
            </div>
          )}

          {/* Amount + Currency */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 18 }}>
            <div>
              <label style={labelStyle}>
                Amount <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                min="0.01"
                style={inputStyle(!!errors.amount)}
              />
              {errors.amount && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.amount}</div>}
            </div>
            <div>
              <label style={labelStyle}>Currency</label>
              <input type="text" value={billingCurrency} disabled style={{ ...inputStyle(false), background: '#F5F6FC', color: '#6b7280', cursor: 'not-allowed' }} />
              <div style={{ fontSize: 12, color: '#7C85C0', marginTop: 4 }}>From project billing currency</div>
            </div>
          </div>

          {/* Exchange Rate + INR Preview */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
            <div>
              <label style={labelStyle}>
                Exchange Rate {!isInr && <span style={{ color: '#ef4444' }}>*</span>}
              </label>
              <input
                type="number"
                value={isInr ? '1' : exchangeRate}
                onChange={(e) => setExchangeRate(e.target.value)}
                disabled={isInr}
                step="0.0001"
                min="0.0001"
                style={{ ...inputStyle(!!errors.exchange_rate), ...(isInr ? { background: '#F5F6FC', color: '#6b7280', cursor: 'not-allowed' } : {}) }}
              />
              <div style={{ fontSize: 12, color: '#7C85C0', marginTop: 4 }}>
                {isInr ? 'Auto-set to 1.0 for INR' : `1 ${billingCurrency} = INR. Manual entry required.`}
              </div>
              {errors.exchange_rate && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.exchange_rate}</div>}
            </div>
            <div>
              <label style={labelStyle}>INR Preview</label>
              <div style={{
                background: 'linear-gradient(135deg, rgba(43,57,144,0.05), rgba(74,91,181,0.03))',
                border: '1px solid #E8EAF6', borderRadius: 8, padding: '10px 14px',
              }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#2B3990' }}>{formatInr(amountInr)}</div>
                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                  {amountNum.toLocaleString()} × {exchangeRateNum || 0} = {formatInr(amountInr)}
                </div>
              </div>
            </div>
          </div>

          {/* Invoice Date */}
          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>
              Invoice Date <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="date"
              value={invoiceDate}
              onChange={(e) => setInvoiceDate(e.target.value)}
              style={inputStyle(false)}
            />
          </div>

          {/* Billing Period (T&M / Onboarding only) */}
          {!isFP && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
              <div>
                <label style={labelStyle}>Billing Period Start</label>
                <input type="date" value={billingStart} onChange={(e) => setBillingStart(e.target.value)} style={inputStyle(false)} />
              </div>
              <div>
                <label style={labelStyle}>Billing Period End</label>
                <input type="date" value={billingEnd} onChange={(e) => setBillingEnd(e.target.value)} style={inputStyle(false)} />
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label style={labelStyle}>Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any additional notes for this invoice..."
              style={{ ...inputStyle(false), minHeight: 80, resize: 'vertical' }}
            />
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 24px 20px', borderTop: '1px solid #E8EAF6', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button
            onClick={onClose}
            style={{ padding: '10px 20px', border: '1px solid #D6DAF0', borderRadius: 8, fontSize: 14, cursor: 'pointer', background: '#fff', color: '#1e1b4b' }}
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
            {saveMutation.isPending ? 'Saving...' : editingInvoice ? 'Update Invoice' : 'Save Invoice'}
          </button>
        </div>
      </div>
    </div>
  )
}
