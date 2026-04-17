import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Bell,
  Shield,
  AlertTriangle,
  FileText,
  Settings,
  Activity,
} from 'lucide-react'

const nav = [
  { to: '/',          label: 'Dashboard',       icon: LayoutDashboard },
  { to: '/alerts',    label: 'Alerts',           icon: Bell },
  { to: '/threats',   label: 'Threat Intel',     icon: Shield },
  { to: '/incidents', label: 'Incidents',        icon: AlertTriangle },
  { to: '/logs',      label: 'Log Viewer',       icon: FileText },
]

export function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-siem-surface border-r border-siem-border flex flex-col shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-siem-border">
        <div className="w-8 h-8 bg-siem-accent rounded-lg flex items-center justify-center">
          <Activity size={18} className="text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-siem-text leading-tight">SIEM Platform</p>
          <p className="text-xs text-siem-muted">Security Operations</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-siem-accent/20 text-siem-accent font-medium'
                  : 'text-siem-muted hover:text-siem-text hover:bg-white/5'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom settings */}
      <div className="px-3 py-4 border-t border-siem-border">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-siem-muted hover:text-siem-text hover:bg-white/5 transition-colors"
        >
          <Settings size={16} />
          Settings
        </NavLink>
      </div>
    </aside>
  )
}
