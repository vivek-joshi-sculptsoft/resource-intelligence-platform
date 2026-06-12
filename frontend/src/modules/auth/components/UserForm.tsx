import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createUser, fetchRoles, fetchUser, updateUser } from '../users-api'

function EyeOpenIcon() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeClosedIcon() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  fontSize: '14px',
  border: '1.5px solid #D6DAF0',
  borderRadius: '8px',
  color: '#1e1b4b',
  outline: 'none',
  transition: 'border-color 0.15s, box-shadow 0.15s',
  background: '#fff',
}

const selectStyle = {
  ...inputStyle,
  appearance: 'none' as const,
  cursor: 'pointer',
  paddingRight: '36px',
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 12px center',
}

function focusInput(e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) {
  e.target.style.borderColor = '#4A5BB5'
  e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'
}

function blurInput(e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) {
  e.target.style.borderColor = '#D6DAF0'
  e.target.style.boxShadow = 'none'
}

export function UserForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [roleId, setRoleId] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: fetchRoles,
  })

  const { data: existingUser } = useQuery({
    queryKey: ['user', id],
    queryFn: () => fetchUser(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existingUser) {
      setName(existingUser.name)
      setEmail(existingUser.email)
      setRoleId(existingUser.role.id)
      setIsActive(existingUser.is_active)
    }
  }, [existingUser])

  const roles = rolesData?.data ?? []

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      if (isEdit) {
        await updateUser(id!, {
          name,
          role_id: roleId,
          is_active: isActive,
          ...(password ? { password } : {}),
        })
        toast.success('User updated successfully')
      } else {
        await createUser({ email, name, password, role_id: roleId })
        toast.success('User created successfully')
      }
      queryClient.invalidateQueries({ queryKey: ['users'] })
      navigate('/admin/users')
    } catch (err: any) {
      setError(err.response?.data?.message || 'An error occurred')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-5 flex items-center gap-2 text-[13px]" style={{ color: '#7C85C0' }}>
        <a href="#" onClick={(e) => { e.preventDefault(); navigate('/admin/users') }} className="no-underline transition-colors hover:underline" style={{ color: '#7C85C0' }}>Settings</a>
        <span className="text-[11px]">/</span>
        <a href="#" onClick={(e) => { e.preventDefault(); navigate('/admin/users') }} className="no-underline transition-colors hover:underline" style={{ color: '#7C85C0' }}>Users</a>
        <span className="text-[11px]">/</span>
        <span className="font-semibold" style={{ color: '#1e1b4b' }}>{isEdit ? 'Edit User' : 'Add New User'}</span>
      </div>

      {/* Form Card */}
      <div
        className="max-w-[640px] rounded-xl p-8"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}
      >
        <h2 className="mb-1 text-[19px] font-bold tracking-tight" style={{ color: '#1e1b4b' }}>
          {isEdit ? `Edit User` : 'Add New User'}
        </h2>
        <p className="mb-7 text-[13px]" style={{ color: '#7C85C0' }}>
          {isEdit ? 'Update account details and permissions.' : 'Create a new login account for the platform.'}
        </p>

        <form onSubmit={handleSubmit}>
          {/* Name */}
          <div className="mb-[22px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Full Name <span className="text-[14px] font-bold leading-none" style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Enter full name"
              style={inputStyle}
              onFocus={focusInput}
              onBlur={blurInput}
            />
          </div>

          {/* Email */}
          <div className="mb-[22px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Email Address <span className="text-[14px] font-bold leading-none" style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isEdit}
              placeholder="name@sculptsoft.com"
              style={{ ...inputStyle, ...(isEdit ? { background: '#F0F1FA', color: '#6b7280' } : {}) }}
              onFocus={focusInput}
              onBlur={blurInput}
            />
          </div>

          {/* Password */}
          <div className="mb-[22px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Password {!isEdit && <span className="text-[14px] font-bold leading-none" style={{ color: '#ef4444' }}>*</span>}
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEdit}
                minLength={8}
                placeholder={isEdit ? 'Leave blank to keep current password' : 'Minimum 8 characters'}
                style={{ ...inputStyle, paddingRight: '44px' }}
                onFocus={focusInput}
                onBlur={blurInput}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center justify-center rounded border-none bg-transparent p-1 transition-colors"
                style={{ color: '#7C85C0', cursor: 'pointer' }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = '#2B3990' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = '#7C85C0' }}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeClosedIcon /> : <EyeOpenIcon />}
              </button>
            </div>
            <div className="mt-1.5 text-[12px]" style={{ color: '#7C85C0' }}>Must be at least 8 characters</div>
          </div>

          {/* Role */}
          <div className="mb-[22px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Role <span className="text-[14px] font-bold leading-none" style={{ color: '#ef4444' }}>*</span>
            </label>
            <select
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              required
              style={selectStyle}
              onFocus={focusInput as any}
              onBlur={blurInput as any}
            >
              <option value="" disabled>Select role...</option>
              {roles.map((r: any) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          {/* Link to Resource (optional) */}
          <div className="mb-[22px]">
            <label className="mb-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Link to Resource
            </label>
            <select
              style={selectStyle}
              onFocus={focusInput as any}
              onBlur={blurInput as any}
            >
              <option value="">None (no resource link)</option>
            </select>
            <div className="mt-1.5 text-[12px]" style={{ color: '#7C85C0' }}>Optional. Links this login to a resource profile.</div>
          </div>

          {/* Active Toggle (edit mode only) */}
          {isEdit && (
            <>
              <div className="my-6 h-px" style={{ background: '#E8EAF6' }} />
              <div
                className="mb-[22px] flex items-center justify-between rounded-lg p-4"
                style={{ background: '#F0F1FA', border: '1.5px solid #E8EAF6' }}
              >
                <div>
                  <div className="flex items-center gap-2.5 text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
                    Account Active
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold"
                      style={{
                        background: isActive ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                        color: isActive ? '#16a34a' : '#ef4444',
                      }}
                    >
                      {isActive ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="mt-0.5 text-[12px]" style={{ color: '#7C85C0' }}>
                    Deactivating will prevent this user from logging in
                  </div>
                </div>
                <label className="relative inline-block h-[26px] w-[48px] shrink-0 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="peer absolute h-0 w-0 opacity-0"
                  />
                  <span
                    className="absolute inset-0 rounded-full transition-colors duration-200 before:absolute before:left-[3px] before:top-[3px] before:h-5 before:w-5 before:rounded-full before:bg-white before:shadow-[0_1px_3px_rgba(0,0,0,0.15)] before:transition-transform before:duration-200 peer-checked:before:translate-x-[22px]"
                    style={{ background: isActive ? '#22c55e' : '#D6DAF0' }}
                  />
                </label>
              </div>
            </>
          )}

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg p-3 text-[13px]" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }}>
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-8 flex justify-end gap-3 border-t pt-6" style={{ borderColor: '#E8EAF6' }}>
            <button
              type="button"
              onClick={() => navigate('/admin/users')}
              className="rounded-lg px-6 py-2.5 text-[14px] font-semibold transition-all"
              style={{ background: '#fff', border: '1.5px solid #D6DAF0', color: '#6b7280' }}
              onMouseEnter={(e) => { const t = e.currentTarget; t.style.background = '#F0F1FA'; t.style.borderColor = '#4A5BB5'; t.style.color = '#1e1b4b' }}
              onMouseLeave={(e) => { const t = e.currentTarget; t.style.background = '#fff'; t.style.borderColor = '#D6DAF0'; t.style.color = '#6b7280' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 rounded-lg border-none px-6 py-2.5 text-[14px] font-semibold text-white transition-all hover:-translate-y-px disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #FF4B2B, #FF6B4A)', boxShadow: '0 2px 8px rgba(255,75,43,0.3)' }}
            >
              {isEdit ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  {submitting ? 'Saving...' : 'Save Changes'}
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  {submitting ? 'Creating...' : 'Create User'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
