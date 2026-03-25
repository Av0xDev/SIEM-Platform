import type { Alert, Incident, ThreatFeed, LogEntry, DashboardStats } from '../types'

// Mock data for demo/offline mode
export const mockAlerts: Alert[] = [
  { id: 1, title: 'Brute Force Attack Detected', description: 'Multiple failed login attempts from 192.168.1.100', severity: 'CRITICAL', status: 'OPEN', sourceIp: '192.168.1.100', destinationIp: '10.0.0.5', createdAt: new Date(Date.now() - 300000).toISOString(), count: 47 },
  { id: 2, title: 'Port Scan Detected', description: 'Sequential port scanning activity from external host', severity: 'HIGH', status: 'IN_PROGRESS', sourceIp: '45.33.32.156', destinationIp: '10.0.0.0/24', createdAt: new Date(Date.now() - 900000).toISOString(), count: 1024 },
  { id: 3, title: 'Suspicious Outbound Traffic', description: 'Unusual data transfer to unknown external host', severity: 'HIGH', status: 'OPEN', sourceIp: '10.0.0.42', destinationIp: '185.220.101.45', createdAt: new Date(Date.now() - 1800000).toISOString() },
  { id: 4, title: 'Malware Signature Detected', description: 'Known malware hash found in file system', severity: 'CRITICAL', status: 'IN_PROGRESS', sourceIp: '10.0.0.15', createdAt: new Date(Date.now() - 3600000).toISOString() },
  { id: 5, title: 'Unauthorized Admin Access', description: 'Login to admin panel from unusual location', severity: 'HIGH', status: 'RESOLVED', sourceIp: '203.0.113.45', destinationIp: '10.0.0.1', createdAt: new Date(Date.now() - 7200000).toISOString() },
  { id: 6, title: 'SQL Injection Attempt', description: 'SQL injection payload detected in web request', severity: 'MEDIUM', status: 'CLOSED', sourceIp: '198.51.100.22', destinationIp: '10.0.0.80', createdAt: new Date(Date.now() - 10800000).toISOString() },
  { id: 7, title: 'Privilege Escalation Attempt', description: 'User attempted to escalate privileges via sudo', severity: 'HIGH', status: 'OPEN', sourceIp: '10.0.0.22', createdAt: new Date(Date.now() - 14400000).toISOString() },
  { id: 8, title: 'DDoS Traffic Detected', description: 'High volume of traffic from multiple sources', severity: 'CRITICAL', status: 'IN_PROGRESS', sourceIp: '0.0.0.0/0', destinationIp: '10.0.0.1', createdAt: new Date(Date.now() - 18000000).toISOString(), count: 50000 },
  { id: 9, title: 'Phishing Email Received', description: 'Email with malicious attachment detected', severity: 'MEDIUM', status: 'RESOLVED', createdAt: new Date(Date.now() - 21600000).toISOString() },
  { id: 10, title: 'Certificate Expiry Warning', description: 'SSL certificate expires in 7 days', severity: 'LOW', status: 'OPEN', createdAt: new Date(Date.now() - 86400000).toISOString() },
]

export const mockIncidents: Incident[] = [
  { id: 1, title: 'Active Brute Force Campaign', description: 'Ongoing brute force attack against SSH servers', severity: 'CRITICAL', status: 'INVESTIGATING', createdAt: new Date(Date.now() - 600000).toISOString(), alertIds: [1, 7] },
  { id: 2, title: 'DDoS Attack in Progress', description: 'Distributed denial-of-service attack affecting production', severity: 'CRITICAL', status: 'ACTIVE', createdAt: new Date(Date.now() - 1800000).toISOString(), alertIds: [8] },
  { id: 3, title: 'Malware Infection Detected', description: 'Workstation compromised with Trojan', severity: 'HIGH', status: 'CONTAINED', createdAt: new Date(Date.now() - 3600000).toISOString(), alertIds: [4] },
  { id: 4, title: 'Data Exfiltration Attempt', description: 'Suspicious outbound data transfer investigated', severity: 'HIGH', status: 'RESOLVED', createdAt: new Date(Date.now() - 7200000).toISOString(), alertIds: [3] },
]

export const mockThreatFeeds: ThreatFeed[] = [
  { id: 1, indicator: '192.168.1.100', type: 'IP', severity: 'CRITICAL', confidence: 95, description: 'Known botnet C2 server', source: 'VirusTotal', lastSeen: new Date(Date.now() - 86400000).toISOString() },
  { id: 2, indicator: '45.33.32.156', type: 'IP', severity: 'HIGH', confidence: 87, description: 'Port scanner, multiple reports', source: 'AbuseIPDB', lastSeen: new Date(Date.now() - 172800000).toISOString() },
  { id: 3, indicator: 'malware.example.com', type: 'DOMAIN', severity: 'CRITICAL', confidence: 99, description: 'Malware distribution domain', source: 'Threat Intel Feed', lastSeen: new Date(Date.now() - 3600000).toISOString() },
  { id: 4, indicator: '44d88612fea8a8f36de82e1278abb02f', type: 'HASH', severity: 'HIGH', confidence: 92, description: 'EICAR test malware signature', source: 'MISP', lastSeen: new Date(Date.now() - 259200000).toISOString() },
  { id: 5, indicator: 'CVE-2024-1234', type: 'CVE', severity: 'CRITICAL', confidence: 100, description: 'Remote code execution in OpenSSL', source: 'NVD', lastSeen: new Date().toISOString() },
  { id: 6, indicator: '185.220.101.45', type: 'IP', severity: 'HIGH', confidence: 78, description: 'Tor exit node', source: 'TorExitNodes', lastSeen: new Date(Date.now() - 43200000).toISOString() },
  { id: 7, indicator: 'phishing-bank.tk', type: 'DOMAIN', severity: 'MEDIUM', confidence: 72, description: 'Phishing site impersonating bank', source: 'PhishTank', lastSeen: new Date(Date.now() - 432000000).toISOString() },
  { id: 8, indicator: '203.0.113.45', type: 'IP', severity: 'MEDIUM', confidence: 65, description: 'Scanning activity observed', source: 'Shodan', lastSeen: new Date(Date.now() - 604800000).toISOString() },
]

export const mockLogs: LogEntry[] = Array.from({ length: 50 }, (_, i) => {
  const severities = ['INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const
  const sources = ['firewall', 'webserver', 'auth', 'ids', 'endpoint', 'dns']
  const messages = [
    'Connection established from 192.168.1.1:49382',
    'Failed login attempt for user "admin"',
    'File access denied: /etc/shadow',
    'Outbound connection blocked to 185.220.101.45:443',
    'DNS query for malware.example.com from 10.0.0.22',
    'Process spawned: cmd.exe -enc <base64>',
    'Registry modification detected: HKLM\\Run',
    'Large file transfer: 2.4GB to 203.0.113.45',
    'Certificate validation failed for api.example.com',
    'Memory spike detected in svchost.exe (87%)',
  ]
  const s = severities[Math.floor(Math.random() * severities.length)]
  return {
    id: `log-${i}`,
    timestamp: new Date(Date.now() - i * 120000).toISOString(),
    source: sources[Math.floor(Math.random() * sources.length)],
    severity: s,
    message: messages[Math.floor(Math.random() * messages.length)],
    host: `host-${Math.floor(Math.random() * 10) + 1}.corp`,
    category: sources[Math.floor(Math.random() * sources.length)],
  }
})

export const mockStats: DashboardStats = {
  totalAlerts: mockAlerts.length,
  criticalAlerts: mockAlerts.filter((a) => a.severity === 'CRITICAL').length,
  openIncidents: mockIncidents.filter((i) => i.status === 'ACTIVE' || i.status === 'INVESTIGATING').length,
  threatIndicators: mockThreatFeeds.length,
  resolvedToday: 3,
  avgResponseTime: 24,
}
