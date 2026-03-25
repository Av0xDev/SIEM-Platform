import { useState, useEffect } from 'react'
import { Search, Filter, RefreshCw, ChevronDown } from 'lucide-react'
import { AlertBadge } from '../components/AlertBadge'
import { mockAlerts } from '../utils/mockData'
import { getAlerts, respondToAlert } from '../api/alerts'
import type { Alert, Severity, AlertStatus } from '../types'
import { formatDistanceToNow, format } from 'date-fns'

const STATUS_CLASSES: Record<AlertStatus, string> = {
  OPEN:        'text-orange-400 bg-orange-400/10 border-orange-400/20',
  IN_PROGRESS: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  RESOLVED:    'text-green-400 bg-green-400/10 border-green-400/20',
  CLOSED:      'text-gray-400 bg-gray-400/10 border-gray-400/20',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts)
  const [selected, setSelected] = useState<Alert | null>(null)
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(mockAlerts.length)

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const res = await getAlerts({ severity: filterSeverity, status: filterStatus, search, page, limit: 15 })
      if (res.alerts?.length) {
        setAlerts(res.alerts)
        setTotal(res.total)
      }
    } catch {
      // keep mock data
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAlerts() }, [filterSeverity, filterStatus, page, search])

  const filtered = alerts.filter((a) => {
    const q = search.toLowerCase()
    const matchSearch = !search || a.title.toLowerCase().includes(q) || (a.sourceIp ?? '').includes(q) || (a.destinationIp ?? '').includes(q)
    const matchSeverity = !filterSeverity || a.severity === filterSeverity
    const matchStatus = !filterStatus || a.status === filterStatus
    return matchSearch && matchSeverity && matchStatus
  })

  const handleRespond = async (alert: Alert, action: string) => {
    try {
      await respondToAlert(alert.id, action)
      setAlerts((prev) => prev.map((a) => a.id === alert.id ? { ...a, status: 'IN_PROGRESS' } : a))
    } catch {
      // demo: just update locally
      setAlerts((prev) => prev.map((a) => a.id === alert.id ? { ...a, status: 'IN_PROGRESS' } : a))
    }
    if (selected?.id === alert.id) setSelected({ ...alert, status: 'IN_PROGRESS' })
  }

  return (
    <div className="flex h-full gap-4">
      {/* Alert list */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-siem-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search alerts, IPs…"
              className="w-full bg-siem-surface border border-siem-border rounded-lg pl-9 pr-4 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
            />
          </div>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-siem-surface border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
          >
            <option value="">All Severities</option>
            {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] as Severity[]).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-siem-surface border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
          >
            <option value="">All Statuses</option>
            {(['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'] as AlertStatus[]).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <button
            onClick={fetchAlerts}
            className="p-2 bg-siem-surface border border-siem-border rounded-lg text-siem-muted hover:text-siem-text transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Summary pills */}
        <div className="flex items-center gap-2 mb-3 text-xs text-siem-muted">
          <span>{total} total</span>
          {['CRITICAL','HIGH','MEDIUM','LOW'].map((s) => {
            const cnt = filtered.filter((a) => a.severity === s).length
            if (!cnt) return null
            return (
              <span key={s} className={`px-2 py-0.5 rounded-full border ${
                s==='CRITICAL' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                s==='HIGH' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                s==='MEDIUM' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                'bg-blue-500/10 text-blue-400 border-blue-500/20'
              }`}>{s}: {cnt}</span>
            )
          })}
        </div>

        {/* Table */}
        <div className="bg-siem-surface border border-siem-border rounded-lg overflow-hidden flex-1">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-siem-border bg-siem-bg">
                  <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium">Severity</th>
                  <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium">Title</th>
                  <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden md:table-cell">Source IP</th>
                  <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden lg:table-cell">Status</th>
                  <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden lg:table-cell">Time</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((alert) => (
                  <tr
                    key={alert.id}
                    onClick={() => setSelected(alert)}
                    className={`border-b border-siem-border/50 hover:bg-white/5 cursor-pointer transition-colors ${
                      selected?.id === alert.id ? 'bg-siem-accent/5' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <AlertBadge severity={alert.severity} />
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-siem-text font-medium truncate max-w-xs">{alert.title}</p>
                      <p className="text-xs text-siem-muted truncate max-w-xs hidden sm:block">{alert.description}</p>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="font-mono text-xs text-siem-muted">{alert.sourceIp ?? '—'}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className={`text-xs px-2 py-0.5 rounded border font-mono ${STATUS_CLASSES[alert.status]}`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell text-xs text-siem-muted">
                      {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-3 text-xs text-siem-muted">
          <span>Showing {filtered.length} of {total}</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="px-2 py-1 rounded bg-siem-surface border border-siem-border disabled:opacity-40">←</button>
            <span>Page {page}</span>
            <button onClick={() => setPage(page + 1)} className="px-2 py-1 rounded bg-siem-surface border border-siem-border">→</button>
          </div>
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-80 shrink-0 bg-siem-surface border border-siem-border rounded-lg p-5 overflow-y-auto">
          <div className="flex items-start justify-between mb-4">
            <h2 className="text-sm font-semibold text-siem-text">Alert Details</h2>
            <button onClick={() => setSelected(null)} className="text-siem-muted hover:text-siem-text text-lg leading-none">&times;</button>
          </div>

          <div className="space-y-3 text-sm">
            <div>
              <AlertBadge severity={selected.severity} />
              <h3 className="text-siem-text font-medium mt-2">{selected.title}</h3>
              <p className="text-siem-muted text-xs mt-1">{selected.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                ['Status', selected.status],
                ['ID', String(selected.id)],
                ['Source', selected.sourceIp ?? '—'],
                ['Destination', selected.destinationIp ?? '—'],
                ['Created', format(new Date(selected.createdAt), 'MM/dd HH:mm')],
                ['Count', selected.count ? String(selected.count) : '1'],
              ].map(([label, val]) => (
                <div key={label} className="bg-siem-bg rounded p-2">
                  <p className="text-siem-muted">{label}</p>
                  <p className="text-siem-text font-mono truncate">{val}</p>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="pt-2 space-y-2">
              <p className="text-xs font-medium text-siem-muted uppercase tracking-wide">Actions</p>
              <button
                onClick={() => handleRespond(selected, 'acknowledge')}
                className="w-full bg-siem-accent/10 hover:bg-siem-accent/20 text-siem-accent border border-siem-accent/30 rounded-lg py-2 text-xs font-medium transition-colors"
              >
                Acknowledge Alert
              </button>
              <button
                onClick={() => handleRespond(selected, 'escalate')}
                className="w-full bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 border border-orange-500/30 rounded-lg py-2 text-xs font-medium transition-colors"
              >
                Escalate to Incident
              </button>
              <button
                onClick={() => handleRespond(selected, 'resolve')}
                className="w-full bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg py-2 text-xs font-medium transition-colors"
              >
                Mark Resolved
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
