import { Bell, LogOut, User } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'

interface Props {
  pageTitle: string
}

export function Header({ pageTitle }: Props) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 bg-siem-surface border-b border-siem-border flex items-center justify-between px-6 shrink-0">
      <h1 className="text-base font-semibold text-siem-text">{pageTitle}</h1>

      <div className="flex items-center gap-4">
        {/* Notification bell */}
        <button className="relative p-2 text-siem-muted hover:text-siem-text rounded-lg hover:bg-white/5 transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
        </button>

        {/* User info */}
        <div className="flex items-center gap-2 text-sm">
          <div className="w-7 h-7 bg-siem-accent/20 rounded-full flex items-center justify-center">
            <User size={14} className="text-siem-accent" />
          </div>
          <span className="text-siem-text font-medium">{user?.username ?? 'admin'}</span>
          <span className="text-xs text-siem-muted bg-siem-bg px-1.5 py-0.5 rounded">
            {user?.role ?? 'ADMIN'}
          </span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="p-2 text-siem-muted hover:text-red-400 rounded-lg hover:bg-red-500/10 transition-colors"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}
