import apiClient from './client'
import type { Incident } from '../types'
import type { PlaybookResult } from '../types'

export const getIncidents = async (): Promise<{ incidents: Incident[] }> => {
  const { data } = await apiClient.get('/api/incidents')
  return data
}

export const getIncident = async (id: string | number): Promise<Incident> => {
  const { data } = await apiClient.get(`/api/incidents/${id}`)
  return data
}

export const executePlaybook = async (playbookName: string, context: Record<string, unknown>): Promise<PlaybookResult> => {
  const { data } = await apiClient.post('/api/playbooks/execute', { playbook: playbookName, context })
  return data
}

export const getPlaybooks = async (): Promise<{ playbooks: string[] }> => {
  const { data } = await apiClient.get('/api/playbooks')
  return data
}
