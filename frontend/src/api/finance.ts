import { apiClient } from './client'

export type PaymentMethod = 'especes' | 'banque'

export interface SupplierInvoiceLine {
  id: number
  product_id: number
  qty: number
  unit_price: number
  subtotal: number
}

export interface SupplierInvoice {
  id: number
  reference: string
  move_type: 'bill' | 'debit_note'
  purchase_order_id: number | null
  origin_invoice_id: number | null
  supplier_id: number
  invoice_date: string
  state: 'draft' | 'validated' | 'cancelled'
  amount_total: number
  amount_paid: number
  amount_due: number
  payment_state: 'not_paid' | 'partially_paid' | 'paid'
  lines: SupplierInvoiceLine[]
}

export const listSupplierInvoices = async (): Promise<SupplierInvoice[]> =>
  (await apiClient.get<SupplierInvoice[]>('/supplier-invoices')).data

export const createSupplierInvoiceFromOrder = async (purchaseOrderId: number): Promise<SupplierInvoice> =>
  (await apiClient.post<SupplierInvoice>('/supplier-invoices/from-order', { purchase_order_id: purchaseOrderId })).data

export const validateSupplierInvoice = async (id: number): Promise<SupplierInvoice> =>
  (await apiClient.post<SupplierInvoice>(`/supplier-invoices/${id}/validate`)).data

export const cancelSupplierInvoice = async (id: number): Promise<SupplierInvoice> =>
  (await apiClient.post<SupplierInvoice>(`/supplier-invoices/${id}/cancel`)).data

export interface SupplierPayment {
  id: number
  reference: string
  invoice_id: number
  amount: number
  payment_date: string
  state: 'draft' | 'confirmed' | 'cancelled'
  payment_method: PaymentMethod
  cash_session_id: number | null
  bank_account_id: number | null
}

export interface CreateSupplierPaymentInput {
  invoice_id: number
  amount: number
  payment_date: string
  payment_method: PaymentMethod
  cash_session_id?: number
  bank_account_id?: number
}

export const listSupplierPayments = async (): Promise<SupplierPayment[]> =>
  (await apiClient.get<SupplierPayment[]>('/supplier-payments')).data

export const createSupplierPayment = async (input: CreateSupplierPaymentInput): Promise<SupplierPayment> =>
  (await apiClient.post<SupplierPayment>('/supplier-payments', input)).data

export const confirmSupplierPayment = async (id: number): Promise<SupplierPayment> =>
  (await apiClient.post<SupplierPayment>(`/supplier-payments/${id}/confirm`)).data

export const getSupplierBalance = async (partnerId: number): Promise<{ balance: number }> =>
  (await apiClient.get<{ balance: number }>(`/partners/${partnerId}/supplier-balance`)).data

export interface CashRegister {
  id: number
  name: string
  code: string
  branch_id: number | null
  active: boolean
}

export const listCashRegisters = async (): Promise<CashRegister[]> =>
  (await apiClient.get<CashRegister[]>('/cash-registers')).data

export const createCashRegister = async (input: { name: string; code: string }): Promise<CashRegister> =>
  (await apiClient.post<CashRegister>('/cash-registers', input)).data

export interface CashSession {
  id: number
  register_id: number
  state: 'open' | 'closed'
  opening_balance: number
  closing_balance: number | null
  opened_at: string
  closed_at: string | null
  computed_balance: number
  variance: number | null
}

export const listCashSessions = async (): Promise<CashSession[]> =>
  (await apiClient.get<CashSession[]>('/cash-sessions')).data

export const openCashSession = async (input: { register_id: number; opening_balance: number }): Promise<CashSession> =>
  (await apiClient.post<CashSession>('/cash-sessions', input)).data

export const closeCashSession = async (id: number, closingBalance: number): Promise<CashSession> =>
  (await apiClient.post<CashSession>(`/cash-sessions/${id}/close`, { closing_balance: closingBalance })).data

export interface BankAccount {
  id: number
  name: string
  bank_name: string
  account_number: string
  opening_balance: number
  active: boolean
  balance: number
}

export const listBankAccounts = async (): Promise<BankAccount[]> =>
  (await apiClient.get<BankAccount[]>('/bank-accounts')).data

export const createBankAccount = async (input: {
  name: string
  bank_name: string
  account_number: string
  opening_balance?: number
}): Promise<BankAccount> => (await apiClient.post<BankAccount>('/bank-accounts', input)).data

export interface BankTransaction {
  id: number
  bank_account_id: number
  movement_type: 'in' | 'out'
  amount: number
  reason: string | null
  transaction_date: string
}

export const listBankTransactions = async (): Promise<BankTransaction[]> =>
  (await apiClient.get<BankTransaction[]>('/bank-transactions')).data

export const createBankTransaction = async (input: {
  bank_account_id: number
  movement_type: 'in' | 'out'
  amount: number
  reason?: string
  transaction_date: string
}): Promise<BankTransaction> => (await apiClient.post<BankTransaction>('/bank-transactions', input)).data

export interface Expense {
  id: number
  reference: string
  category: string
  description: string | null
  amount: number
  expense_date: string
  branch_id: number | null
  state: 'draft' | 'validated' | 'cancelled'
  payment_method: PaymentMethod
  cash_session_id: number | null
  bank_account_id: number | null
}

export const listExpenses = async (): Promise<Expense[]> => (await apiClient.get<Expense[]>('/expenses')).data

export const createExpense = async (input: {
  category: string
  description?: string
  amount: number
  expense_date: string
  payment_method: PaymentMethod
  cash_session_id?: number
  bank_account_id?: number
}): Promise<Expense> => (await apiClient.post<Expense>('/expenses', input)).data

export const validateExpense = async (id: number): Promise<Expense> =>
  (await apiClient.post<Expense>(`/expenses/${id}/validate`)).data

export const cancelExpense = async (id: number): Promise<Expense> =>
  (await apiClient.post<Expense>(`/expenses/${id}/cancel`)).data
