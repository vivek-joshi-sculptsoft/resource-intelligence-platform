import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'

function EyeOpenIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeClosedIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
      <path d="M14.12 14.12a3 3 0 11-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function LogoIcon() {
  return <img src="/logo.png" alt="SculptNexus" className="mb-4 h-20 w-auto" />
}

export function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)

  if (isLoading) return null
  if (isAuthenticated) return <Navigate to="/" replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid email or password. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6" style={{ background: 'linear-gradient(135deg, #1B2B65, #2B3990, #4A5BB5)' }}>
      <div className="w-full max-w-[420px] animate-[cardEntrance_0.6s_cubic-bezier(0.22,1,0.36,1)_forwards] rounded-xl bg-white px-9 pt-10 pb-9 shadow-[0_8px_32px_rgba(43,57,144,0.2)]">
        {/* Logo & Title */}
        <div className="mb-7 flex flex-col items-center">
          <LogoIcon />
          <div className="mt-1 text-[13px] font-medium tracking-wide" style={{ color: '#7C85C0' }}>
            by SculptSoft
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 animate-[alertSlide_0.3s_ease-out]">
            <svg className="mt-0.5 h-[18px] w-[18px] shrink-0 text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            <span className="flex-1 text-[13.5px] leading-snug text-red-900">{error}</span>
            <button
              type="button"
              onClick={() => setError('')}
              className="shrink-0 rounded p-0.5 text-red-700 transition-colors hover:bg-red-100"
              aria-label="Dismiss error"
            >
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-[18px]">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="name@company.com"
              className="h-11 w-full rounded-lg px-3.5 text-[14.5px] outline-none transition-all duration-200"
              style={{
                color: '#1e1b4b',
                border: '1.5px solid #D6DAF0',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#2B3990'
                e.target.style.boxShadow = '0 0 0 3px rgba(43, 57, 144, 0.12)'
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#D6DAF0'
                e.target.style.boxShadow = 'none'
              }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter your password"
                className="h-11 w-full rounded-lg pr-[46px] pl-3.5 text-[14.5px] outline-none transition-all duration-200"
                style={{
                  color: '#1e1b4b',
                  border: '1.5px solid #D6DAF0',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#2B3990'
                  e.target.style.boxShadow = '0 0 0 3px rgba(43, 57, 144, 0.12)'
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#D6DAF0'
                  e.target.style.boxShadow = 'none'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-1.5 top-1/2 flex -translate-y-1/2 items-center justify-center rounded-md p-1.5 transition-colors hover:bg-[#F0F1FA]"
                style={{ color: '#7C85C0' }}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeClosedIcon /> : <EyeOpenIcon />}
              </button>
            </div>
          </div>

          <div className="-mt-1 flex items-center justify-between">
            <label className="flex cursor-pointer select-none items-center gap-2">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded"
                style={{ accentColor: '#2B3990' }}
              />
              <span className="text-[13.5px]" style={{ color: '#6b7280' }}>Remember me</span>
            </label>
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              className="text-[13.5px] font-medium no-underline transition-colors hover:underline"
              style={{ color: '#2B3990' }}
            >
              Forgot password?
            </a>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="mt-1 h-[46px] w-full cursor-pointer rounded-lg border-none text-[15px] font-semibold tracking-wide text-white transition-all duration-150 hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(255,75,43,0.35)] active:translate-y-0 active:shadow-[0_2px_8px_rgba(255,75,43,0.25)] disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #FF4B2B, #FF6B4A)' }}
          >
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>

      <div className="mt-8 text-center text-[12.5px] tracking-wide" style={{ color: 'rgba(255, 255, 255, 0.5)' }}>
        &copy; 2026 SculptSoft. All rights reserved.
      </div>
    </div>
  )
}
