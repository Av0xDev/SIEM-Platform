import apiClient from './client'
import type { ThreatFeed } from '../types'

export interface ThreatIntelResponse {
  feeds: ThreatFeed[]
  total: number
  stats: {
    critical: number
    high: number
    medium: number
    low: number
  }
}

export interface IOCLookupResult {
  indicator: string
  type: string
  found: boolean
  severity?: string
  confidence?: number
  description?: string
  riskScore: number
  sources?: string[]
}

export const getThreatIntel = async (params?: { type?: string; search?: string }): Promise<ThreatIntelResponse> => {
  const query = new URLSearchParams(params as Record<string, string>)
  const { data } = await apiClient.get(`/api/threat-intel?${query}`)
  return data
}

export const lookupIOC = async (indicator: string, type?: string): Promise<IOCLookupResult> => {
  const { data } = await apiClient.post('/api/threat-intel/lookup', { indicator, type })
  return data
}
