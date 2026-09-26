import { apiClient } from './client'

export interface SalesSummary {
  total_confirmed_sales: number
  total_invoiced: number
  total_collected: number
}

export const getSalesSummary = async (periodStart: string, periodEnd: string): Promise<SalesSummary> =>
  (
    await apiClient.get<SalesSummary>('/reports/sales-summary', {
      params: { period_start: periodStart, period_end: periodEnd },
    })
  ).data

export interface HrSummary {
  active_employee_count: number
  on_leave_today_count: number
  payroll_cost: number
}

export const getHrSummary = async (periodStart: string, periodEnd: string): Promise<HrSummary> =>
  (
    await apiClient.get<HrSummary>('/reports/hr-summary', {
      params: { period_start: periodStart, period_end: periodEnd },
    })
  ).data
