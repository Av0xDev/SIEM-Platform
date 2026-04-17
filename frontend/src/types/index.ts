// TypeScript types for the SIEM Platform

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type AlertStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type IncidentStatus = 'ACTIVE' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED' | 'CLOSED';
export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  createdAt: string;
}

export interface Alert {
  id: string | number;
  title: string;
  description: string;
  severity: Severity;
  status: AlertStatus;
  sourceIp?: string;
  destinationIp?: string;
  createdAt: string;
  updatedAt?: string;
  correlationId?: string;
  assignedTo?: string;
  tags?: string[];
  count?: number;
}

export interface Incident {
  id: string | number;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  alertIds?: (string | number)[];
  assignedTo?: string;
  createdAt: string;
  updatedAt?: string;
  playbookExecuted?: string;
  timeline?: IncidentEvent[];
}

export interface IncidentEvent {
  timestamp: string;
  action: string;
  actor: string;
  details?: string;
}

export interface ThreatFeed {
  id: string | number;
  indicator: string;
  type: 'IP' | 'DOMAIN' | 'HASH' | 'URL' | 'CVE';
  severity: Severity;
  confidence: number;
  description?: string;
  source: string;
  lastSeen: string;
  tags?: string[];
}

export interface LogEntry {
  id?: string;
  timestamp: string;
  source: string;
  severity: Severity;
  message: string;
  host?: string;
  category?: string;
  raw?: string;
  parsed?: Record<string, unknown>;
}

export interface DashboardStats {
  totalAlerts: number;
  criticalAlerts: number;
  openIncidents: number;
  threatIndicators: number;
  resolvedToday: number;
  avgResponseTime?: number;
}

export interface AlertsBySeverity {
  severity: Severity;
  count: number;
}

export interface PlaybookResult {
  jobId: string;
  status: 'success' | 'failed' | 'running';
  playbookName: string;
  actionsTaken: string[];
  startedAt: string;
  completedAt?: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}
