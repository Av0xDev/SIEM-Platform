import { useState, useEffect } from 'react'
import { Search, Database, ExternalLink } from 'lucide-react'
import { AlertBadge } from '../components/AlertBadge'
import { mockThreatFeeds } from '../utils/mockData'
import { getThreatIntel, lookupIOC } from '../api/threatIntel'
import type { ThreatFeed } from '../types'
import { formatDistanceToNow } from 'date-fns'

const TYPE_COLORS: Record<string, string> = {
  IP:     'text-blue-400 bg-blue-400/10 border-blue-400/20',
  DOMAIN: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
  HASH:   'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  URL:    'text-orange-400 bg-orange-400/10 border-orange-400/20',
  CVE:    'text-red-400 bg-red-400/10 border-red-400/20',
}

export default function ThreatIntelPage() {
  const [feeds, setFeeds] = useState<ThreatFeed[]>(mockThreatFeeds)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [iocQuery, setIocQuery] = useState('')
  const [iocResult, setIocResult] = useState<null | { found: boolean; riskScore: number; description?: string; severity?: string }>(null)
  const [lookupLoading, setLookupLoading] = useState(false)

  useEffect(() => {
    getThreatIntel({ type: filterType, search })
      .then((res) => { if (res.feeds?.length) setFeeds(res.feeds) })
      .catch(() => {})
  }, [filterType, search])

  const handleLookup = async () => {
    if (!iocQuery) return
    setLookupLoading(true)
    try {
      const res = await lookupIOC(iocQuery)
      setIocResult(res)
    } catch {
      // demo mode — check mock feeds
      const found = mockThreatFeeds.find((f) =>
        f.indicator.toLowerCase().includes(iocQuery.toLowerCase())
      )
      setIocResult(found
        ? { found: true, riskScore: found.confidence, description: found.description, severity: found.severity }
        : { found: false, riskScore: 0 })
    } finally {
      setLookupLoading(false)
    }
  }

  const filtered = feeds.filter((f) => {
    const q = search.toLowerCase()
    const matchSearch = !search || f.indicator.toLowerCase().includes(q) || (f.description ?? '').toLowerCase().includes(q)
    const matchType = !filterType || f.type === filterType
    return matchSearch && matchType
  })

  const stats = {
    critical: filtered.filter((f) => f.severity === 'CRITICAL').length,
    high: filtered.filter((f) => f.severity === 'HIGH').length,
    medium: filtered.filter((f) => f.severity === 'MEDIUM').length,
    low: filtered.filter((f) => f.severity === 'LOW').length,
  }

  return (
    <div className="space-y-6">
      {/* IOC Lookup */}
      <div className="bg-siem-surface border border-siem-border rounded-lg p-5">
        <h2 className="text-sm font-semibold text-siem-text mb-3 flex items-center gap-2">
          <Search size={14} />
          IOC Lookup
        </h2>
        <div className="flex gap-3">
          <input
            value={iocQuery}
            onChange={(e) => setIocQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
            placeholder="Enter IP, domain, hash, or CVE…"
            className="flex-1 bg-siem-bg border border-siem-border rounded-lg px-4 py-2 text-sm text-siem-text outline-none focus:border-siem-accent font-mono"
          />
          <button
            onClick={handleLookup}
            disabled={lookupLoading || !iocQuery}
            className="bg-siem-accent hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {lookupLoading ? 'Looking up…' : 'Lookup'}
          </button>
        </div>

        {iocResult && (
          <div className={`mt-3 p-3 rounded-lg border text-sm ${
            iocResult.found
              ? 'bg-red-500/10 border-red-500/30 text-red-300'
              : 'bg-green-500/10 border-green-500/30 text-green-300'
          }`}>
            {iocResult.found ? (
              <div className="space-y-1">
                <p className="font-semibold">⚠ Malicious indicator found</p>
                <p className="text-xs">Severity: <strong>{iocResult.severity}</strong> · Confidence: {iocResult.riskScore}%</p>
                {iocResult.description && <p className="text-xs">{iocResult.description}</p>}
              </div>
            ) : (
              <p>✓ Indicator not found in threat database</p>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Critical', count: stats.critical, color: 'text-red-400 bg-red-500/10 border-red-500/20' },
          { label: 'High', count: stats.high, color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
          { label: 'Medium', count: stats.medium, color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Low', count: stats.low, color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
        ].map(({ label, count, color }) => (
          <div key={label} className={`rounded-lg border p-3 text-center ${color}`}>
            <p className="text-2xl font-bold">{count}</p>
            <p className="text-xs mt-0.5 opacity-80">{label}</p>
          </div>
        ))}
      </div>

      {/* Threat feed table */}
      <div className="bg-siem-surface border border-siem-border rounded-lg">
        {/* Toolbar */}
        <div className="flex items-center gap-3 p-4 border-b border-siem-border">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-siem-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search indicators…"
              className="w-full bg-siem-bg border border-siem-border rounded-lg pl-9 pr-4 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-siem-bg border border-siem-border rounded-lg px-3 py-2 text-sm text-siem-text outline-none focus:border-siem-accent"
          >
            <option value="">All Types</option>
            {['IP', 'DOMAIN', 'HASH', 'URL', 'CVE'].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <div className="flex items-center gap-1.5 text-xs text-siem-muted">
            <Database size={12} />
            {filtered.length} indicators
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-siem-border bg-siem-bg">
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium">Indicator</th>
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium">Type</th>
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium">Severity</th>
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden md:table-cell">Confidence</th>
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden lg:table-cell">Source</th>
                <th className="text-left px-4 py-3 text-xs text-siem-muted font-medium hidden lg:table-cell">Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((feed) => (
                <tr key={feed.id} className="group border-b border-siem-border/50 hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-siem-text">{feed.indicator}</span>
                      <ExternalLink size={12} className="text-siem-muted opacity-0 group-hover:opacity-100" />
                    </div>
                    {feed.description && <p className="text-xs text-siem-muted mt-0.5 truncate max-w-xs">{feed.description}</p>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded border font-mono ${TYPE_COLORS[feed.type] ?? 'text-gray-400 bg-gray-400/10 border-gray-400/20'}`}>
                      {feed.type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <AlertBadge severity={feed.severity} />
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-siem-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-siem-accent rounded-full"
                          style={{ width: `${feed.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-siem-muted font-mono">{feed.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-xs text-siem-muted">{feed.source}</td>
                  <td className="px-4 py-3 hidden lg:table-cell text-xs text-siem-muted">
                    {formatDistanceToNow(new Date(feed.lastSeen), { addSuffix: true })}
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
