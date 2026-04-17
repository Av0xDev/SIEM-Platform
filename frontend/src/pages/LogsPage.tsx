import { useState, useEffect, useRef } from 'react'
import { Search, RefreshCw, Upload } from 'lucide-react'
import { AlertBadge } from '../components/AlertBadge'
import { mockLogs } from '../utils/mockData'
import { getLogs, ingestLog } from '../api/logs'
import type { LogEntry, Severity } from '../types'
import { format } from 'date-fns'

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>(mockLogs)
  const [search, setSearch] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterSource, setFilterSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [ingestForm, setIngestForm] = useState({ message: '', source: 'manual', severity: 'INFO' as Severity })
  const [ingestStatus, setIngestStatus] = useState('')
  const tableRef = useRef<HTMLDivElement>(null)

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const res = await getLogs({ severity: filterSeverity, source: filterSource, search, limit: 100 })
      if (res.logs?.length) setLogs(res.logs)
    } catch {
      // keep mock data
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchLogs() }, [filterSeverity, filterSource, search])

  // Simulate streaming
  useEffect(() => {
    if (!streaming) return
    const MESSAGES = [
      'SSH login successful for user root from 10.0.0.5',
      'HTTP 403 on /admin from 45.33.32.156',
      'DNS resolution failed for malware.example.com',
      'ICMP sweep detected from 192.168.100.50',
      'New process spawned: powershell.exe -NoProfile',
    ]
    const interval = setInterval(() => {
      const newLog: LogEntry = {
        id: `stream-${Date.now()}`,
        timestamp: new Date().toISOString(),
        source: ['firewall', 'ids', 'auth', 'dns'][Math.floor(Math.random() * 4)],
        severity: (['INFO', 'MEDIUM', 'HIGH', 'CRITICAL'] as Severity[])[Math.floor(Math.random() * 4)],
        message: MESSAGES[Math.floor(Math.random() * MESSAGES.length)],
        host: `host-${Math.floor(Math.random() * 5) + 1}.corp`,
      }
      setLogs((prev) => [newLog, ...prev.slice(0, 199)])
    }, 2000)
    return () => clearInterval(interval)
  }, [streaming])

  const handleIngest = async () => {
    if (!ingestForm.message) return
    try {
      await ingestLog(ingestForm)
      setIngestStatus('✓ Log ingested successfully')
    } catch {
      // demo mode
      const newEntry: LogEntry = {
        id: `manual-${Date.now()}`,
        ...ingestForm,
        timestamp: new Date().toISOString(),
      }
      setLogs((prev) => [newEntry, ...prev])
      setIngestStatus('✓ Log added (demo mode)')
    }
    setTimeout(() => setIngestStatus(''), 3000)
    setIngestForm((f) => ({ ...f, message: '' }))
  }

  const filtered = logs.filter((l) => {
    const q = search.toLowerCase()
    const matchSearch = !search || l.message.toLowerCase().includes(q) || (l.host ?? '').toLowerCase().includes(q) || l.source.toLowerCase().includes(q)
    const matchSeverity = !filterSeverity || l.severity === filterSeverity
    const matchSource = !filterSource || l.source === filterSource
    return matchSearch && matchSeverity && matchSource
  })

  const sources = [...new Set(logs.map((l) => l.source))].sort()

  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Ingest form */}
      <div className="bg-siem-surface border border-siem-border rounded-lg p-4 shrink-0">
        <h2 className="text-sm font-semibold text-siem-text mb-3 flex items-center gap-2">
          <Upload size={14} />
          Log Ingestion
        </h2>
        <div className="flex gap-3 flex-wrap">
          <input
            value={ingestForm.message}
            onChange={(e) => setIngestForm((f) => ({ ...f, message: e.target.value }))}
            onKeyDown={(e) => e.key === 'Enter' && handleIngest()}
            placeholder="Enter log message…"
            className="flex-1 min-w-48 bg-siem-bg border border-siem-border rounded-lg px-4 py-2 text-sm text-siem-text outline-none focus:border-siem-accent font-mono"
          />
          <input
            value={ingestForm.source}
            onChange={(e) => setIngestForm((f) => ({ ...f, source: e.target.value }))}
            placeholder="Source"
            className="w-32 bg-siem-bg border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
          />
          <select
            value={ingestForm.severity}
            onChange={(e) => setIngestForm((f) => ({ ...f, severity: e.target.value as Severity }))}
            className="bg-siem-bg border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
          >
            {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] as Severity[]).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            onClick={handleIngest}
            className="bg-siem-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Ingest
          </button>
        </div>
        {ingestStatus && <p className="text-xs text-green-400 mt-2">{ingestStatus}</p>}
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-siem-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search logs…"
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
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="bg-siem-surface border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
        >
          <option value="">All Sources</option>
          {sources.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <button
          onClick={() => setStreaming((s) => !s)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
            streaming
              ? 'bg-green-500/20 border-green-500/40 text-green-400'
              : 'bg-siem-surface border-siem-border text-siem-muted hover:text-siem-text'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${streaming ? 'bg-green-400 animate-pulse' : 'bg-siem-muted'}`} />
          {streaming ? 'Live' : 'Stream'}
        </button>

        <button
          onClick={fetchLogs}
          className="p-2 bg-siem-surface border border-siem-border rounded-lg text-siem-muted hover:text-siem-text transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Log count */}
      <div className="text-xs text-siem-muted shrink-0">
        Showing {filtered.length} of {logs.length} entries
      </div>

      {/* Log table */}
      <div ref={tableRef} className="flex-1 bg-siem-surface border border-siem-border rounded-lg overflow-hidden">
        <div className="overflow-auto h-full">
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10">
              <tr className="bg-siem-bg border-b border-siem-border">
                <th className="text-left px-3 py-2.5 text-siem-muted font-medium w-36">Timestamp</th>
                <th className="text-left px-3 py-2.5 text-siem-muted font-medium w-20">Severity</th>
                <th className="text-left px-3 py-2.5 text-siem-muted font-medium w-24">Source</th>
                <th className="text-left px-3 py-2.5 text-siem-muted font-medium w-28 hidden lg:table-cell">Host</th>
                <th className="text-left px-3 py-2.5 text-siem-muted font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log, i) => (
                <tr key={log.id ?? i} className="border-b border-siem-border/40 hover:bg-white/5 font-mono">
                  <td className="px-3 py-2 text-siem-muted whitespace-nowrap">
                    {format(new Date(log.timestamp), 'MM/dd HH:mm:ss')}
                  </td>
                  <td className="px-3 py-2">
                    <AlertBadge severity={log.severity} />
                  </td>
                  <td className="px-3 py-2 text-siem-muted">{log.source}</td>
                  <td className="px-3 py-2 text-siem-muted hidden lg:table-cell">{log.host ?? '—'}</td>
                  <td className="px-3 py-2 text-siem-text max-w-0">
                    <p className="truncate">{log.message}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
