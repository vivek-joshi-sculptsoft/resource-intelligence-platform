import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  Building2,
  BarChart3,
  UserCheck,
  Clock,
  ClipboardList,
  Settings,
  UserPlus,
  ChevronDown,
  LogOut,
  Bell,
  PanelLeftClose,
  PanelLeftOpen,
  Receipt,
} from 'lucide-react'

interface NavItem {
  label: string
  to: string
  icon: React.ReactNode
  allowedRoles?: string[]
}

const MAIN_NAV: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard size={18} /> },
  { label: 'Resources', to: '/resources', icon: <Users size={18} /> },
  {
    label: 'Clients',
    to: '/clients',
    icon: <Building2 size={18} />,
    allowedRoles: ['CEO', 'CTO', 'DM', 'PM', 'FINANCE', 'HR'],
  },
  {
    label: 'Projects',
    to: '/projects',
    icon: <FolderOpen size={18} />,
    allowedRoles: ['CEO', 'CTO', 'DM', 'PM', 'FINANCE', 'HR'],
  },
  {
    label: 'Dashboards',
    to: '/utilization',
    icon: <BarChart3 size={18} />,
    allowedRoles: ['CEO', 'CTO', 'DM', 'PM', 'FINANCE', 'HR'],
  },
  {
    label: 'Availability',
    to: '/availability',
    icon: <UserCheck size={18} />,
  },
  {
    label: 'My Assignments',
    to: '/my-assignments',
    icon: <ClipboardList size={18} />,
    allowedRoles: ['ENGINEER'],
  },
  {
    label: 'Worklogs',
    to: '/worklogs',
    icon: <Clock size={18} />,
    allowedRoles: ['CEO', 'CTO', 'DM', 'PM', 'FINANCE', 'HR'],
  },
  {
    label: 'Receivables',
    to: '/receivables',
    icon: <Receipt size={18} />,
    allowedRoles: ['CEO', 'CTO', 'FINANCE'],
  },
]

const ADMIN_NAV: NavItem[] = [
  {
    label: 'Users',
    to: '/admin/users',
    icon: <UserPlus size={18} />,
    allowedRoles: ['CEO', 'CTO'],
  },
  {
    label: 'Roles',
    to: '/admin/roles',
    icon: <Settings size={18} />,
    allowedRoles: ['CEO', 'CTO'],
  },
]

function filterByRole(items: NavItem[], roleCode: string | undefined): NavItem[] {
  if (!roleCode) return []
  return items.filter((item) => !item.allowedRoles || item.allowedRoles.includes(roleCode))
}

export function RootLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const roleCode = user?.role?.code
  const visibleMain = filterByRole(MAIN_NAV, roleCode)
  const visibleAdmin = filterByRole(ADMIN_NAV, roleCode)

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
          <img src="/logo-icon.png" alt="SculptNexus" className="h-[34px] w-auto" />
          {!collapsed && (
            <div className="flex items-baseline gap-1.5 text-[16px] font-bold tracking-tight">
              <span>
                <span style={{ color: '#0A0E1F' }}>Sculpt</span>
                <span style={{ color: '#2254F4' }}>Nexus</span>
              </span>
              <span
                className="rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                style={{ background: '#FFF3D6', color: '#B7791F' }}
              >
                Beta
              </span>
              <span className="text-[12px] font-medium" style={{ color: '#7C85C0' }}>
                - A Resource Intelligence Platform By & For SculptSoft
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-[18px]">
          <button
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border-none transition-colors"
            style={{ background: '#F0F1FA' }}
          >
            <Bell size={20} style={{ color: '#6b7280' }} />
          </button>

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
              <ChevronDown
                size={16}
                style={{
                  color: '#7C85C0',
                  transform: dropdownOpen ? 'rotate(180deg)' : 'none',
                  transition: 'transform 0.2s',
                }}
              />
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
                    <LogOut size={16} />
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
          className="flex shrink-0 flex-col overflow-y-auto py-5 transition-all duration-200"
          style={{
            width: collapsed ? '64px' : '240px',
            background: '#F5F6FC',
            borderRight: '1px solid #E8EAF6',
          }}
        >
          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="mx-auto mb-3 flex h-8 w-8 items-center justify-center rounded-lg border-none transition-colors"
            style={{ background: 'transparent', color: '#7C85C0', cursor: 'pointer' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#E8EAF6' }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>

          {!collapsed && (
            <div className="px-5 pb-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em]" style={{ color: '#7C85C0' }}>
              Main
            </div>
          )}
          {visibleMain.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center border-l-[3px] text-[13.5px] font-medium no-underline transition-all ${
                  isActive ? 'font-semibold' : 'border-transparent'
                } ${collapsed ? 'justify-center px-0 py-[9px]' : 'gap-2.5 px-5 py-[9px]'}`
              }
              style={({ isActive }) => ({
                color: isActive ? '#2B3990' : '#6b7280',
                background: isActive ? 'rgba(43,57,144,0.06)' : 'transparent',
                borderLeftColor: isActive ? '#FF4B2B' : 'transparent',
              })}
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && item.label}
            </NavLink>
          ))}

          {visibleAdmin.length > 0 && (
            <>
              <div className="mx-4 my-2 h-px" style={{ background: '#E8EAF6' }} />
              {!collapsed && (
                <div className="px-5 pb-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em]" style={{ color: '#7C85C0' }}>
                  Settings
                </div>
              )}
              {visibleAdmin.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={false}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center border-l-[3px] text-[13.5px] font-medium no-underline transition-all ${
                      isActive ? 'font-semibold' : 'border-transparent'
                    } ${collapsed ? 'justify-center px-0 py-[9px]' : 'gap-2.5 px-5 py-[9px]'}`
                  }
                  style={({ isActive }) => ({
                    color: isActive ? '#2B3990' : '#6b7280',
                    background: isActive ? 'rgba(43,57,144,0.06)' : 'transparent',
                    borderLeftColor: isActive ? '#2B3990' : 'transparent',
                  })}
                >
                  <span className="shrink-0">{item.icon}</span>
                  {!collapsed && item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto" style={{ padding: '28px 36px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
