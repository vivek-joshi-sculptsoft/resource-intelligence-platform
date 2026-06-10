import { Outlet } from 'react-router'

export function RootLayout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar placeholder — built in S4-01 */}
      <aside className="w-64 border-r bg-gray-50 p-4">
        <h2 className="text-lg font-semibold">RI Platform</h2>
        <p className="mt-2 text-sm text-gray-500">Sidebar placeholder</p>
      </aside>

      <main className="flex-1 overflow-auto">
        {/* Top bar placeholder — built in S4-01 */}
        <header className="border-b bg-white px-6 py-3">
          <span className="text-sm text-gray-500">Top bar placeholder</span>
        </header>

        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
