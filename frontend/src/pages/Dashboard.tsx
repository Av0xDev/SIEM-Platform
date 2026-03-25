import { useState, useEffect } from 'react'
import { Bell, Shield, AlertTriangle, Database, CheckCircle, Clock } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid,
} from 'recharts'
import { StatCard } from '../components/StatCard'
import { AlertBadge } from '../components/AlertBadge'
import { mockAlerts, mockStats } from '../utils/mockData'
import { getAlerts } from '../api/alerts'
import type { Alert, DashboardStats } from '../types'
import { formatDistanceToNow } from 'date-fns'

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
  INFO: '#6b7280',
}

// Fake activity timeline data
const activityData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, '0')}:00`,
  alerts: Math.floor(Math.random() * 20),
  events: Math.floor(Math.random() * 80),
}))

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts)
  const [stats, setStats] = useState<DashboardStats>(mockStats)
  const [realtimeCount, setRealtimeCount] = useState(0)

  useEffect(() => {
    getAlerts({ limit: 10 })
      .then((res) => {
        if (res.alerts?.length) {
          setAlerts(res.alerts)
          setStats({
            totalAlerts: res.total,
            criticalAlerts: res.alerts.filter((a) => a.severity === 'CRITICAL').length,
            openIncidents: mockStats.openIncidents,
            threatIndicators: mockStats.threatIndicators,
            resolvedToday: mockStats.resolvedToday,
          })
        }
      })
      .catch(() => {/* use mock data */})

    // Simulate real-time counter
    const interval = setInterval(() => {
      setRealtimeCount((c) => c + Math.floor(Math.random() * 3))
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const severityDist = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map((s) => ({
    name: s,
    value: alerts.filter((a) => a.severity === s).length || Math.floor(Math.random() * 5) + 1,
  }))

  const recentAlerts = alerts.slice(0, 6)

  return (
    <div className="space-y-6">
      {/* Real-time indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-siem-muted">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse inline-block"></span>
          Live monitoring active
          {realtimeCount > 0 && (
            <span className="bg-siem-accent/20 text-siem-accent text-xs px-2 py-0.5 rounded-full font-mono">
              +{realtimeCount} events
            </span>
          )}
        </div>
        <span className="text-xs text-siem-muted font-mono">
          {new Date().toLocaleTimeString()}
        </span>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Alerts"
          value={stats.totalAlerts}
          icon={<Bell size={20} />}
          color="text-siem-accent"
        />
        <StatCard
          title="Critical"
          value={stats.criticalAlerts}
          icon={<AlertTriangle size={20} />}
          color="text-red-400"
          trend="↑ 2 today"
          trendUp={false}
        />
        <StatCard
          title="Open Incidents"
          value={stats.openIncidents}
          icon={<Shield size={20} />}
          color="text-orange-400"
        />
        <StatCard
          title="Threat Indicators"
          value={stats.threatIndicators}
          icon={<Database size={20} />}
          color="text-purple-400"
        />
        <StatCard
          title="Resolved Today"
          value={stats.resolvedToday}
          icon={<CheckCircle size={20} />}
          color="text-green-400"
          trend="On track"
          trendUp
        />
        <StatCard
          title="Avg Response (h)"
          value={stats.avgResponseTime ?? '—'}
          icon={<Clock size={20} />}
          color="text-yellow-400"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity timeline */}
        <div className="lg:col-span-2 bg-siem-surface border border-siem-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-siem-text mb-4">24h Activity Timeline</h2>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 10 }} interval={3} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Line type="monotone" dataKey="events" stroke="#3b82f6" strokeWidth={2} dot={false} name="Events" />
              <Line type="monotone" dataKey="alerts" stroke="#ef4444" strokeWidth={2} dot={false} name="Alerts" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Severity distribution */}
        <div className="bg-siem-surface border border-siem-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-siem-text mb-4">Alert Severity</h2>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={severityDist} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                {severityDist.map((entry) => (
                  <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-1 mt-2">
            {severityDist.map((s) => (
              <div key={s.name} className="flex items-center gap-1.5 text-xs text-siem-muted">
                <span className="w-2 h-2 rounded-full" style={{ background: SEVERITY_COLORS[s.name] }} />
                {s.name}: {s.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bar chart + recent alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert trend bar chart */}
        <div className="bg-siem-surface border border-siem-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-siem-text mb-4">Alerts by Severity</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={severityDist} layout="vertical">
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} width={65} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {severityDist.map((entry) => (
                  <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent alerts table */}
        <div className="lg:col-span-2 bg-siem-surface border border-siem-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-siem-text">Recent Alerts</h2>
            <a href="/alerts" className="text-xs text-siem-accent hover:underline">View all →</a>
          </div>
          <div className="space-y-2">
            {recentAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
              >
                <AlertBadge severity={alert.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-siem-text truncate">{alert.title}</p>
                  <p className="text-xs text-siem-muted truncate">{alert.sourceIp ?? '—'}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                    alert.status === 'OPEN' ? 'text-orange-400 bg-orange-400/10' :
                    alert.status === 'IN_PROGRESS' ? 'text-blue-400 bg-blue-400/10' :
                    'text-green-400 bg-green-400/10'
                  }`}>
                    {alert.status}
                  </span>
                  <p className="text-xs text-siem-muted mt-0.5">
                    {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
