import apiClient from './client'
import type { Alert } from '../types'

export interface AlertsResponse {
  alerts: Alert[]
  total: number
  page: number
  pages: number
}

export interface AlertFilters {
  severity?: string
  status?: string
  page?: number
  limit?: number
  search?: string
}

export const getAlerts = async (filters: AlertFilters = {}): Promise<AlertsResponse> => {
  const params = new URLSearchParams()
  if (filters.severity) params.append('severity', filters.severity)
  if (filters.status) params.append('status', filters.status)
  if (filters.page) params.append('page', String(filters.page))
  if (filters.limit) params.append('limit', String(filters.limit))
  if (filters.search) params.append('search', filters.search)

  const { data } = await apiClient.get(`/api/alerts?${params}`)
  return data
}

export const getAlert = async (id: string | number): Promise<Alert> => {
  const { data } = await apiClient.get(`/api/alerts/${id}`)
  return data
}

export const respondToAlert = async (id: string | number, action: string): Promise<unknown> => {
  const { data } = await apiClient.post(`/api/alerts/${id}/respond`, { action })
  return data
}

export const updateAlertStatus = async (id: string | number, status: string): Promise<Alert> => {
  const { data } = await apiClient.patch(`/api/alerts/${id}`, { status })
  return data
}
