import { apiClient } from './client'

export interface SaleOrderLine {
  id: number
  product_id: number
  qty: number
  unit_price: number
  discount_percent: number
  subtotal: number
}

export interface SaleOrder {
  id: number
  reference: string
  customer_id: number
  branch_id: number | null
  order_date: string
  state: 'devis' | 'commande' | 'terminee' | 'annulee'
  amount_total: number
  lines: SaleOrderLine[]
}

export interface CreateSaleOrderInput {
  customer_id: number
  order_date: string
  lines: { product_id: number; qty: number; unit_price: number; discount_percent?: number }[]
}

export const listSaleOrders = async (): Promise<SaleOrder[]> =>
  (await apiClient.get<SaleOrder[]>('/sale-orders')).data

export const createSaleOrder = async (input: CreateSaleOrderInput): Promise<SaleOrder> =>
  (await apiClient.post<SaleOrder>('/sale-orders', input)).data

export const confirmSaleOrder = async (id: number): Promise<SaleOrder> =>
  (await apiClient.post<SaleOrder>(`/sale-orders/${id}/confirm`)).data

export const terminateSaleOrder = async (id: number): Promise<SaleOrder> =>
  (await apiClient.post<SaleOrder>(`/sale-orders/${id}/terminate`)).data

export const cancelSaleOrder = async (id: number): Promise<SaleOrder> =>
  (await apiClient.post<SaleOrder>(`/sale-orders/${id}/cancel`)).data

export interface InvoiceLine {
  id: number
  product_id: number
  qty: number
  unit_price: number
  subtotal: number
}

export interface Invoice {
  id: number
  reference: string
  move_type: 'invoice' | 'credit_note'
  sale_order_id: number | null
  origin_invoice_id: number | null
  customer_id: number
  invoice_date: string
  state: 'draft' | 'validated' | 'cancelled'
  amount_total: number
  amount_paid: number
  amount_due: number
  payment_state: 'not_paid' | 'partially_paid' | 'paid'
  lines: InvoiceLine[]
}

export const listInvoices = async (): Promise<Invoice[]> => (await apiClient.get<Invoice[]>('/invoices')).data

export const createInvoiceFromOrder = async (saleOrderId: number): Promise<Invoice> =>
  (await apiClient.post<Invoice>('/invoices/from-order', { sale_order_id: saleOrderId })).data

export const validateInvoice = async (id: number): Promise<Invoice> =>
  (await apiClient.post<Invoice>(`/invoices/${id}/validate`)).data

export const cancelInvoice = async (id: number): Promise<Invoice> =>
  (await apiClient.post<Invoice>(`/invoices/${id}/cancel`)).data

export interface Payment {
  id: number
  reference: string
  invoice_id: number
  amount: number
  payment_date: string
  state: 'draft' | 'confirmed' | 'cancelled'
}

export const listPayments = async (): Promise<Payment[]> => (await apiClient.get<Payment[]>('/payments')).data

export const createPayment = async (input: {
  invoice_id: number
  amount: number
  payment_date: string
}): Promise<Payment> => (await apiClient.post<Payment>('/payments', input)).data

export const confirmPayment = async (id: number): Promise<Payment> =>
  (await apiClient.post<Payment>(`/payments/${id}/confirm`)).data

export const getPartnerBalance = async (partnerId: number): Promise<{ balance: number }> =>
  (await apiClient.get<{ balance: number }>(`/partners/${partnerId}/balance`)).data
