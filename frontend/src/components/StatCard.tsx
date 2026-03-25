import type { ReactNode } from 'react'

interface Props {
  title: string
  value: string | number
  icon: ReactNode
  color?: string
  trend?: string
  trendUp?: boolean
}

export function StatCard({ title, value, icon, color = 'text-siem-accent', trend, trendUp }: Props) {
  return (
    <div className="bg-siem-surface border border-siem-border rounded-lg p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-siem-bg ${color}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-siem-muted text-sm truncate">{title}</p>
        <p className="text-2xl font-bold text-siem-text mt-0.5">{value}</p>
        {trend && (
          <p className={`text-xs mt-1 ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
            {trendUp ? '↑' : '↓'} {trend}
          </p>
        )}
      </div>
    </div>
  )
}
