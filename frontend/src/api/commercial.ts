import { apiClient } from './client'

export interface SalesRep {
  id: number
  name: string
  user_id: number | null
  commission_rate: number
  active: boolean
}

export const listSalesReps = async (): Promise<SalesRep[]> => (await apiClient.get<SalesRep[]>('/sales-reps')).data

export const createSalesRep = async (input: { name: string; user_id?: number; commission_rate: number }): Promise<SalesRep> =>
  (await apiClient.post<SalesRep>('/sales-reps', input)).data

export const getSalesRepCommission = async (
  repId: number,
  periodStart: string,
  periodEnd: string,
): Promise<{ commission: number }> =>
  (
    await apiClient.get<{ commission: number }>(`/sales-reps/${repId}/commission`, {
      params: { period_start: periodStart, period_end: periodEnd },
    })
  ).data

export interface SalesTarget {
  id: number
  sales_rep_id: number
  period_start: string
  period_end: string
  target_amount: number
  achieved_amount: number
  achievement_percent: number | null
}

export const listSalesTargets = async (): Promise<SalesTarget[]> =>
  (await apiClient.get<SalesTarget[]>('/sales-targets')).data

export const createSalesTarget = async (input: {
  sales_rep_id: number
  period_start: string
  period_end: string
  target_amount: number
}): Promise<SalesTarget> => (await apiClient.post<SalesTarget>('/sales-targets', input)).data
