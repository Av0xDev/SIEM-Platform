import type { Severity } from '../types'

const config: Record<Severity, { label: string; classes: string }> = {
  CRITICAL: { label: 'Critical', classes: 'bg-red-500/20 text-red-400 border border-red-500/40' },
  HIGH:     { label: 'High',     classes: 'bg-orange-500/20 text-orange-400 border border-orange-500/40' },
  MEDIUM:   { label: 'Medium',   classes: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40' },
  LOW:      { label: 'Low',      classes: 'bg-blue-500/20 text-blue-400 border border-blue-500/40' },
  INFO:     { label: 'Info',     classes: 'bg-gray-500/20 text-gray-400 border border-gray-500/40' },
}

interface Props {
  severity: Severity
  className?: string
}

export function AlertBadge({ severity, className = '' }: Props) {
  const { label, classes } = config[severity] ?? config.INFO
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono ${classes} ${className}`}>
      {label}
    </span>
  )
}
