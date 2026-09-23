import { apiClient } from './client'
import type { AuditLogEntry } from './types'

export async function listAuditLogs(): Promise<AuditLogEntry[]> {
  const { data } = await apiClient.get<AuditLogEntry[]>('/audit-logs')
  return data
}
