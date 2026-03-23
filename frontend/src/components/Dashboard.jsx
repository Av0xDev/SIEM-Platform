import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { io } from 'socket.io-client'
import './Dashboard.css'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080'
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8080'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalLogs: 0,
    totalAlerts: 0,
    criticalAlerts: 0,
    systemHealth: 'unknown'
  })
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // Fetch initial stats
    fetchStats()

    // Connect to WebSocket
    const socket = io(WS_URL, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    })

    socket.on('connect', () => {
      setConnected(true)
      console.log('Connected to SIEM Platform')
    })

    socket.on('new_log', (log) => {
      console.log('New log received:', log)
    })

    socket.on('correlation_detected', (correlation) => {
      setAlerts(prev => [correlation, ...prev].slice(0, 10))
    })

    socket.on('disconnect', () => {
      setConnected(false)
    })

    return () => socket.disconnect()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/stats`)
      setStats(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching stats:', error)
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🛡️ SIEM Platform Dashboard</h1>
        <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '✓ Connected' : '✗ Disconnected'}
        </span>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Logs</h3>
          <p className="stat-value">{stats.totalLogs?.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Alerts</h3>
          <p className="stat-value">{stats.totalAlerts}</p>
        </div>
        <div className="stat-card critical">
          <h3>Critical Alerts</h3>
          <p className="stat-value">{stats.criticalAlerts}</p>
        </div>
        <div className="stat-card">
          <h3>System Health</h3>
          <p className="stat-value">{stats.systemHealth}</p>
        </div>
      </div>

      <section className="alerts-section">
        <h2>Recent Alerts</h2>
        {alerts.length === 0 ? (
          <p className="no-data">No alerts detected</p>
        ) : (
          <div className="alerts-list">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`alert alert-${alert.severity}`}>
                <strong>{alert.type}</strong>
                <span className="severity">{alert.severity.toUpperCase()}</span>
                <p>{alert.count || alert.transfers} events from {alert.source}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default Dashboard