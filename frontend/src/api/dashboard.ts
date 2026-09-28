import { apiClient } from './client'
import type { SalesSummary } from './reports'

export interface DashboardCashSession {
  register_id: number
  session_id: number
  balance: number
}

export interface DashboardBankAccount {
  account_id: number
  name: string
  balance: number
}

export interface DashboardLowStockProduct {
  product_id: number
  name: string
  qty_on_hand: number
  min_stock_qty: number
}

export interface DashboardExpiringDocument {
  vehicle_id: number
  document_type: string
  end_date: string
}

export interface DashboardSummary {
  sales: SalesSummary
  hr: {
    active_employee_count: number
    on_leave_today_count: number
    payroll_cost: number
    pending_leave_requests: number
  }
  finance: {
    total_receivables: number
    total_payables: number
    cash_sessions: DashboardCashSession[]
    bank_accounts: DashboardBankAccount[]
  }
  stock: {
    low_stock_products: DashboardLowStockProduct[]
  }
  fleet: {
    expiring_documents: DashboardExpiringDocument[]
  }
  distribution: {
    open_delivery_routes: number
  }
}

export const getDashboardSummary = async (periodStart: string, periodEnd: string): Promise<DashboardSummary> =>
  (
    await apiClient.get<DashboardSummary>('/dashboard/summary', {
      params: { period_start: periodStart, period_end: periodEnd },
    })
  ).data

export interface SalesEvolutionPoint {
  period: string
  invoiced_total: number
  invoice_count: number
}

export const getSalesEvolution = async (
  periodStart: string,
  periodEnd: string,
  granularity: 'day' | 'month',
): Promise<SalesEvolutionPoint[]> =>
  (
    await apiClient.get<SalesEvolutionPoint[]>('/dashboard/sales-evolution', {
      params: { period_start: periodStart, period_end: periodEnd, granularity },
    })
  ).data

export interface SalesByProduct {
  product_id: number
  name: string
  qty: number
  revenue: number
}

export const getSalesByProduct = async (periodStart: string, periodEnd: string): Promise<SalesByProduct[]> =>
  (
    await apiClient.get<SalesByProduct[]>('/dashboard/sales-by-product', {
      params: { period_start: periodStart, period_end: periodEnd },
    })
  ).data

export interface ReceivableAging {
  invoice_id: number
  reference: string
  customer_id: number
  customer_name: string | null
  invoice_date: string
  amount_total: number
  amount_paid: number
  amount_due: number
  age_days: number
}

export const getReceivablesAging = async (): Promise<ReceivableAging[]> =>
  (await apiClient.get<ReceivableAging[]>('/dashboard/receivables-aging')).data
