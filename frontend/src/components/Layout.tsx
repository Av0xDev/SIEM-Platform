import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

const titles: Record<string, string> = {
  '/':          'Dashboard',
  '/alerts':    'Alert Management',
  '/threats':   'Threat Intelligence',
  '/incidents': 'Incident Response',
  '/logs':      'Log Viewer',
  '/settings':  'Settings',
}

export function Layout() {
  const { pathname } = useLocation()
  const title = titles[pathname] ?? 'SIEM Platform'

  return (
    <div className="flex h-screen overflow-hidden bg-siem-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header pageTitle={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
