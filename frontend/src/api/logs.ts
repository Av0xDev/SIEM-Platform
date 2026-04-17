import apiClient from './client'
import type { LogEntry } from '../types'

export interface LogsResponse {
  logs: LogEntry[]
  total: number
}

export interface LogFilters {
  source?: string
  severity?: string
  start?: string
  end?: string
  search?: string
  limit?: number
  page?: number
}

export const getLogs = async (filters: LogFilters = {}): Promise<LogsResponse> => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== '') params.append(k, String(v))
  })
  const { data } = await apiClient.get(`/api/logs?${params}`)
  return data
}

export const ingestLog = async (log: Partial<LogEntry>): Promise<unknown> => {
  const { data } = await apiClient.post('/api/logs/ingest', log)
  return data
}
