// See FSD §2.10 — NonHumanCost create/edit modal
import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { createCost, updateCost, type CostEntry, type CostPayload } from '../api'
import { SearchableSelect } from '../../../shared/components'

const CATEGORIES = [
  { value: 'AI_TOOLS', label: 'AI Tools' },
  { value: 'CLOUD_INFRA', label: 'Cloud Infra' },
  { value: 'DEVICES', label: 'Devices' },
  { value: 'THIRD_PARTY_LICENSE', label: 'Third-Party License' },
  { value: 'OTHER', label: 'Other' },
]

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AED', 'SGD', 'AUD', 'CAD']

interface CostFormModalProps {
  open: boolean
  projectId: string
  editingCost: CostEntry | null
  onClose: () => void
}

interface FormErrors {
  description?: string
  category?: string
  amount?: string
  currency?: string
  exchange_rate?: string
  cost_date?: string
  recurring_end_date?: string
}

function formatInr(val: number): string {
  return val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function CostFormModal({ open, projectId, editingCost, onClose }: CostFormModalProps) {
  const queryClient = useQueryClient()

  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('INR')
  const [exchangeRate, setExchangeRate] = useState('1.0000')
  const [costDate, setCostDate] = useState('')
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurringEndDate, setRecurringEndDate] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})

  useEffect(() => {
    if (!open) return
    if (editingCost) {
      setDescription(editingCost.description)
      setCategory(editingCost.category)
      setAmount(String(editingCost.amount))
      setCurrency(editingCost.currency)
      setExchangeRate(String(editingCost.exchange_rate))
      setCostDate(editingCost.cost_date)
      setIsRecurring(editingCost.is_recurring)
      setRecurringEndDate(editingCost.recurring_end_date ?? '')
    } else {
      setDescription('')
      setCategory('')
      setAmount('')
      setCurrency('INR')
      setExchangeRate('1.0000')
      setCostDate(new Date().toISOString().split('T')[0])
      setIsRecurring(false)
      setRecurringEndDate('')
    }
    setErrors({})
  }, [open, editingCost])

  // Auto-manage exchange rate when currency changes
  function handleCurrencyChange(val: string) {
    setCurrency(val)
    if (val === 'INR') {
      setExchangeRate('1.0000')
    }
  }

  const amountNum = parseFloat(amount) || 0
  const rateNum = parseFloat(exchangeRate) || 0
  const amountInr = amountNum * rateNum

  // See BUSINESS-RULES §7.7 — amount_inr = amount × exchange_rate
  const previewSymbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : '₹'
  const previewFormula = `${previewSymbol}${amountNum.toFixed(2)} × ${rateNum.toFixed(4)} =`

  function validate(): boolean {
    const e: FormErrors = {}
    if (!description.trim()) e.description = 'Description is required'
    if (!category) e.category = 'Category is required'
    if (!amount || amountNum <= 0) e.amount = 'Cost amount must be positive'
    if (!currency) e.currency = 'Currency is required'
    if (currency !== 'INR' && rateNum <= 0) e.exchange_rate = 'Exchange rate must be positive'
    if (!costDate) e.cost_date = 'Cost date is required'
    if (isRecurring && !recurringEndDate) e.recurring_end_date = 'Recurring costs must have an end date'
    if (isRecurring && recurringEndDate && costDate && recurringEndDate <= costDate)
      e.recurring_end_date = 'Recurring end date must be after cost date'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const saveMutation = useMutation({
    mutationFn: (payload: CostPayload) =>
      editingCost
        ? updateCost(projectId, editingCost.id, payload)
        : createCost(projectId, payload),
    onSuccess: () => {
      toast.success(editingCost ? 'Cost updated' : 'Cost added')
      queryClient.invalidateQueries({ queryKey: ['project-costs', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-costs-summary', projectId] })
      onClose()
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || 'Failed to save cost'
      toast.error(msg)
    },
  })

  function handleSave() {
    if (!validate()) return
    const payload: CostPayload = {
      description: description.trim(),
      category,
      amount: amountNum,
      currency,
      exchange_rate: currency === 'INR' ? 1.0 : rateNum,
      cost_date: costDate,
      is_recurring: isRecurring,
      recurring_end_date: isRecurring ? recurringEndDate : null,
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
          width: 560,
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
            {editingCost ? 'Edit Cost' : 'Add Non-Human Cost'}
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
          {/* Description */}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              Description <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., AWS Hosting (ap-south-1)"
              style={{
                width: '100%', padding: '10px 14px', border: `1px solid ${errors.description ? '#ef4444' : '#D6DAF0'}`,
                borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
              }}
            />
            {errors.description && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.description}</div>}
          </div>

          {/* Category */}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              Category <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <SearchableSelect
              value={category}
              onChange={setCategory}
              options={[
                { value: '', label: 'Select category...' },
                ...CATEGORIES,
              ]}
              placeholder="Select category..."
              error={!!errors.category}
            />
            {errors.category && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.category}</div>}
          </div>

          {/* Amount + Currency + Exchange Rate (3-col) */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
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
                Currency <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <SearchableSelect
                value={currency}
                onChange={handleCurrencyChange}
                options={CURRENCIES.map((c) => ({ value: c, label: c }))}
                placeholder="Currency"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
                Exchange Rate <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="number"
                value={exchangeRate}
                onChange={(e) => setExchangeRate(e.target.value)}
                placeholder="1.0000"
                step="0.0001"
                min="0.0001"
                disabled={currency === 'INR'}
                style={{
                  width: '100%', padding: '10px 14px',
                  border: `1px solid ${errors.exchange_rate ? '#ef4444' : '#D6DAF0'}`,
                  borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
                  background: currency === 'INR' ? '#F5F6FC' : '#fff',
                  cursor: currency === 'INR' ? 'not-allowed' : 'text',
                }}
              />
              {errors.exchange_rate && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.exchange_rate}</div>}
            </div>
          </div>

          {/* Live INR Preview */}
          <div
            style={{
              background: 'linear-gradient(135deg, #E0F7FA 0%, #E8F5E9 100%)',
              border: '2px solid #26A69A',
              borderRadius: 12,
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 18,
            }}
          >
            <div>
              <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, color: '#00796B', fontWeight: 600 }}>
                INR Equivalent
              </div>
              <div style={{ fontSize: 12, color: '#00897B', marginTop: 2 }}>{previewFormula}</div>
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: '#00695C' }}>
              ₹{formatInr(amountInr)}
            </div>
          </div>

          {/* Cost Date */}
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
              Cost Date <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="date"
              value={costDate}
              onChange={(e) => setCostDate(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: `1px solid ${errors.cost_date ? '#ef4444' : '#D6DAF0'}`,
                borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
              }}
            />
            {errors.cost_date && <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.cost_date}</div>}
          </div>

          {/* Recurring Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
            <input
              type="checkbox"
              id="isRecurring"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: '#2B3990', cursor: 'pointer' }}
            />
            <label htmlFor="isRecurring" style={{ fontSize: 14, fontWeight: 500, color: '#1e1b4b', cursor: 'pointer' }}>
              This is a recurring cost
            </label>
          </div>

          {/* Recurring End Date (conditional) */}
          {isRecurring && (
            <div style={{ marginBottom: 18 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e1b4b', marginBottom: 6 }}>
                Recurring End Date <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <input
                type="date"
                value={recurringEndDate}
                onChange={(e) => setRecurringEndDate(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px',
                  border: `1px solid ${errors.recurring_end_date ? '#ef4444' : '#D6DAF0'}`,
                  borderRadius: 8, fontSize: 14, color: '#1e1b4b', outline: 'none',
                }}
              />
              <div style={{ fontSize: 12, color: '#7C85C0', marginTop: 4 }}>
                Monthly recurring cost until this date.
              </div>
              {errors.recurring_end_date && (
                <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>{errors.recurring_end_date}</div>
              )}
            </div>
          )}
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
            {saveMutation.isPending ? 'Saving...' : 'Save Cost'}
          </button>
        </div>
      </div>
    </div>
  )
}
