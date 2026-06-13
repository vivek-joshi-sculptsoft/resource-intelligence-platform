import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'

const NAV_ITEMS: { label: string; to: string; icon: React.ReactNode; hiddenForRoles?: string[] }[] = [
  {
    label: 'Dashboard',
    to: '/dashboard',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    label: 'Clients',
    to: '/clients',
    hiddenForRoles: ['ENGINEER'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    label: 'Projects',
    to: '/projects',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    label: 'Resources',
    to: '/resources',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    label: 'Allocations',
    to: '/allocations',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
  },
  {
    label: 'Dashboards',
    to: '/utilization',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    label: 'Worklogs',
    to: '/worklogs',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
]

export function RootLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const initials = user?.name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) ?? '?'

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [dropdownOpen])

  async function handleLogout() {
    setDropdownOpen(false)
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen flex-col" style={{ background: '#F0F1FA' }}>
      {/* Header */}
      <header
        className="flex h-[60px] shrink-0 items-center justify-between px-7"
        style={{ background: '#fff', borderBottom: '1px solid #E8EAF6' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-[34px] w-[34px] items-center justify-center rounded-[9px] text-[15px] font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #2B3990, #4A5BB5)', boxShadow: '0 2px 6px rgba(43,57,144,0.2)' }}
          >
            RI
          </div>
          <div className="text-[16px] font-bold tracking-tight" style={{ color: '#1B2B65' }}>
            Resource Intelligence <span style={{ color: '#FF4B2B' }}>Platform</span>
          </div>
        </div>

        <div className="flex items-center gap-[18px]">
          {/* Notification bell */}
          <button
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border-none transition-colors"
            style={{ background: '#F0F1FA' }}
          >
            <svg className="h-5 w-5" style={{ color: '#6b7280' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </button>

          {/* User profile dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex cursor-pointer items-center gap-2.5 rounded-lg border-none bg-transparent px-2 py-1.5 transition-colors"
              style={{ background: dropdownOpen ? '#F0F1FA' : 'transparent' }}
              onMouseEnter={(e) => { if (!dropdownOpen) (e.currentTarget as HTMLElement).style.background = '#F0F1FA' }}
              onMouseLeave={(e) => { if (!dropdownOpen) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
            >
              <div>
                <div className="text-right text-[13.5px] font-semibold" style={{ color: '#1e1b4b' }}>
                  {user?.name ?? 'User'}
                </div>
                <div className="text-right text-[11.5px]" style={{ color: '#7C85C0' }}>
                  {user?.role?.name ?? 'Role'}
                </div>
              </div>
              <div
                className="flex h-[34px] w-[34px] items-center justify-center rounded-full text-[13px] font-semibold text-white"
                style={{ background: 'linear-gradient(135deg, #4A5BB5, #2B3990)' }}
              >
                {initials}
              </div>
              <svg className="h-4 w-4" style={{ color: '#7C85C0', transform: dropdownOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {dropdownOpen && (
              <div
                className="absolute right-0 top-full z-50 mt-2 w-[240px] overflow-hidden rounded-xl py-1"
                style={{ background: '#fff', boxShadow: '0 8px 32px rgba(43,57,144,0.15), 0 2px 8px rgba(0,0,0,0.08)', border: '1px solid #E8EAF6' }}
              >
                <div className="px-4 py-3" style={{ borderBottom: '1px solid #E8EAF6' }}>
                  <div className="text-[14px] font-semibold" style={{ color: '#1e1b4b' }}>{user?.name}</div>
                  <div className="mt-0.5 text-[12.5px]" style={{ color: '#6b7280' }}>{user?.email}</div>
                  <div className="mt-1">
                    <span
                      className="inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                      style={{ background: '#E8EAF6', color: '#2B3990' }}
                    >
                      {user?.role?.name}
                    </span>
                  </div>
                </div>
                <div className="py-1">
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2.5 border-none bg-transparent px-4 py-2.5 text-left text-[13.5px] font-medium transition-colors"
                    style={{ color: '#ef4444', cursor: 'pointer' }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#fef2f2' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                  >
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Body: Sidebar + Main */}
      <div className="flex min-h-0 flex-1">
        {/* Sidebar */}
        <nav
          className="flex w-[240px] shrink-0 flex-col overflow-y-auto py-5"
          style={{ background: '#F5F6FC', borderRight: '1px solid #E8EAF6' }}
        >
          <div className="px-5 pb-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em]" style={{ color: '#7C85C0' }}>
            Main
          </div>
          {NAV_ITEMS.filter((item) => !item.hiddenForRoles || !user?.role?.code || !item.hiddenForRoles.includes(user.role.code)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 border-l-[3px] px-5 py-[9px] text-[13.5px] font-medium no-underline transition-all ${
                  isActive
                    ? 'font-semibold'
                    : 'border-transparent'
                }`
              }
              style={({ isActive }) => ({
                color: isActive ? '#2B3990' : '#6b7280',
                background: isActive ? 'rgba(43,57,144,0.06)' : 'transparent',
                borderLeftColor: isActive ? '#FF4B2B' : 'transparent',
              })}
            >
              <span className="h-[18px] w-[18px] shrink-0">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}

          <div className="mx-4 my-2 h-px" style={{ background: '#E8EAF6' }} />

          <div className="px-5 pb-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em]" style={{ color: '#7C85C0' }}>
            Settings
          </div>
          <NavLink
            to="/admin/users"
            end={false}
            className={({ isActive }) =>
              `flex items-center gap-2.5 border-l-[3px] px-5 py-[9px] text-[13.5px] font-medium no-underline transition-all ${
                isActive ? 'font-semibold' : 'border-transparent'
              }`
            }
            style={({ isActive }) => ({
              color: isActive ? '#2B3990' : '#6b7280',
              background: isActive ? 'rgba(43,57,144,0.06)' : 'transparent',
              borderLeftColor: isActive ? '#2B3990' : 'transparent',
            })}
          >
            <svg className="h-[18px] w-[18px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" y1="8" x2="19" y2="14" />
              <line x1="22" y1="11" x2="16" y2="11" />
            </svg>
            Users
          </NavLink>
          <NavLink
            to="/admin/roles"
            className={({ isActive }) =>
              `flex items-center gap-2.5 border-l-[3px] px-5 py-[9px] text-[13.5px] font-medium no-underline transition-all ${
                isActive ? 'font-semibold' : 'border-transparent'
              }`
            }
            style={({ isActive }) => ({
              color: isActive ? '#2B3990' : '#6b7280',
              background: isActive ? 'rgba(43,57,144,0.06)' : 'transparent',
              borderLeftColor: isActive ? '#2B3990' : 'transparent',
            })}
          >
            <svg className="h-[18px] w-[18px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Roles
          </NavLink>
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-7" style={{ padding: '28px 36px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
