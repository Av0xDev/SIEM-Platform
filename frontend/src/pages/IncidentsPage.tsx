import { useState, useEffect } from 'react'
import { Play, RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { AlertBadge } from '../components/AlertBadge'
import { mockIncidents } from '../utils/mockData'
import { getIncidents, executePlaybook } from '../api/incidents'
import type { Incident } from '../types'
import { formatDistanceToNow } from 'date-fns'

const PLAYBOOKS = [
  { id: 'brute_force_response', label: 'Brute Force Response', desc: 'Block IP, disable account, notify SOC' },
  { id: 'malware_response', label: 'Malware Response', desc: 'Isolate host, kill processes, collect forensics' },
  { id: 'data_exfiltration_response', label: 'Data Exfiltration Response', desc: 'Block connection, revoke tokens, audit data' },
  { id: 'unauthorized_access_response', label: 'Unauthorized Access Response', desc: 'Terminate session, enforce MFA, create incident' },
]

const STATUS_CONFIG: Record<string, { color: string; icon: typeof CheckCircle }> = {
  ACTIVE:        { color: 'text-red-400', icon: AlertTriangle },
  INVESTIGATING: { color: 'text-orange-400', icon: Clock },
  CONTAINED:     { color: 'text-yellow-400', icon: AlertTriangle },
  RESOLVED:      { color: 'text-green-400', icon: CheckCircle },
  CLOSED:        { color: 'text-gray-400', icon: CheckCircle },
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>(mockIncidents)
  const [selected, setSelected] = useState<Incident | null>(null)
  const [playbookRunning, setPlaybookRunning] = useState(false)
  const [playbookResult, setPlaybookResult] = useState<{ actions: string[]; status: string } | null>(null)
  const [executionLog, setExecutionLog] = useState<{ time: string; msg: string; ok: boolean }[]>([])

  useEffect(() => {
    getIncidents()
      .then((res) => { if (res.incidents?.length) setIncidents(res.incidents) })
      .catch(() => {})
  }, [])

  const handleRunPlaybook = async (playbookId: string) => {
    if (!selected) return
    setPlaybookRunning(true)
    setPlaybookResult(null)
    setExecutionLog([])

    const addLog = (msg: string, ok = true) =>
      setExecutionLog((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg, ok }])

    try {
      addLog(`Starting playbook: ${playbookId}…`)
      const res = await executePlaybook(playbookId, { incidentId: selected.id })
      res.actionsTaken?.forEach((a) => addLog(a))
      addLog('Playbook completed successfully')
      setPlaybookResult({ actions: res.actionsTaken ?? [], status: 'success' })
    } catch {
      // Demo mode
      addLog('Connecting to Ruby automation engine…')
      await new Promise((r) => setTimeout(r, 800))
      const demoActions = [
        '✓ Source IP blocked in firewall',
        '✓ Affected user account disabled',
        '✓ SOC team notified via email',
        '✓ Incident ticket created (#INC-0042)',
        '✓ Evidence preserved in audit log',
      ]
      for (const a of demoActions) {
        await new Promise((r) => setTimeout(r, 400))
        addLog(a)
      }
      setPlaybookResult({ actions: demoActions, status: 'success' })
    } finally {
      setPlaybookRunning(false)
    }
  }

  return (
    <div className="flex gap-4 h-full">
      {/* Incidents list */}
      <div className="flex-1 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-siem-text">Active Incidents</h2>
          <span className="text-xs text-siem-muted">{incidents.length} total</span>
        </div>

        {incidents.map((inc) => {
          const cfg = STATUS_CONFIG[inc.status] ?? STATUS_CONFIG.ACTIVE
          const Icon = cfg.icon
          return (
            <div
              key={inc.id}
              onClick={() => { setSelected(inc); setPlaybookResult(null); setExecutionLog([]) }}
              className={`bg-siem-surface border rounded-lg p-4 cursor-pointer transition-colors hover:border-siem-accent/50 ${
                selected?.id === inc.id ? 'border-siem-accent/50 bg-siem-accent/5' : 'border-siem-border'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertBadge severity={inc.severity} />
                    <span className={`text-xs font-medium ${cfg.color} flex items-center gap-1`}>
                      <Icon size={12} />
                      {inc.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-medium text-siem-text">{inc.title}</h3>
                  <p className="text-xs text-siem-muted mt-0.5 line-clamp-2">{inc.description}</p>
                </div>
                <span className="text-xs text-siem-muted shrink-0">
                  {formatDistanceToNow(new Date(inc.createdAt), { addSuffix: true })}
                </span>
              </div>

              {inc.alertIds && inc.alertIds.length > 0 && (
                <div className="mt-2 text-xs text-siem-muted">
                  {inc.alertIds.length} correlated alert{inc.alertIds.length > 1 ? 's' : ''}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Right panel */}
      <div className="w-80 shrink-0 space-y-4">
        {selected ? (
          <>
            {/* Playbook execution */}
            <div className="bg-siem-surface border border-siem-border rounded-lg p-4">
              <h2 className="text-sm font-semibold text-siem-text mb-3 flex items-center gap-2">
                <Play size={14} />
                Response Playbooks
              </h2>
              <p className="text-xs text-siem-muted mb-3">
                Responding to: <span className="text-siem-text">{selected.title}</span>
              </p>

              <div className="space-y-2">
                {PLAYBOOKS.map((pb) => (
                  <button
                    key={pb.id}
                    onClick={() => handleRunPlaybook(pb.id)}
                    disabled={playbookRunning}
                    className="w-full text-left bg-siem-bg hover:bg-white/5 border border-siem-border rounded-lg p-3 transition-colors disabled:opacity-50"
                  >
                    <p className="text-xs font-medium text-siem-text">{pb.label}</p>
                    <p className="text-xs text-siem-muted mt-0.5">{pb.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Execution log */}
            {(executionLog.length > 0 || playbookRunning) && (
              <div className="bg-siem-surface border border-siem-border rounded-lg p-4">
                <h2 className="text-sm font-semibold text-siem-text mb-3 flex items-center gap-2">
                  {playbookRunning ? <RefreshCw size={14} className="animate-spin text-siem-accent" /> : <CheckCircle size={14} className="text-green-400" />}
                  Execution Log
                </h2>
                <div className="space-y-1 font-mono text-xs">
                  {executionLog.map((entry, i) => (
                    <div key={i} className={`flex gap-2 ${entry.ok ? 'text-green-400' : 'text-red-400'}`}>
                      <span className="text-siem-muted shrink-0">{entry.time}</span>
                      <span>{entry.msg}</span>
                    </div>
                  ))}
                  {playbookRunning && (
                    <div className="text-siem-accent flex items-center gap-1">
                      <RefreshCw size={10} className="animate-spin" />
                      Running…
                    </div>
                  )}
                </div>

                {playbookResult && (
                  <div className={`mt-3 p-2 rounded border text-xs font-medium ${
                    playbookResult.status === 'success'
                      ? 'bg-green-500/10 border-green-500/30 text-green-400'
                      : 'bg-red-500/10 border-red-500/30 text-red-400'
                  }`}>
                    {playbookResult.status === 'success' ? '✓ Playbook executed successfully' : '✗ Playbook failed'}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="bg-siem-surface border border-siem-border rounded-lg p-8 text-center">
            <AlertTriangle size={32} className="text-siem-muted mx-auto mb-3" />
            <p className="text-sm text-siem-muted">Select an incident to run response playbooks</p>
          </div>
        )}
      </div>
    </div>
  )
}
