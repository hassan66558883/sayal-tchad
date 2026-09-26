import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  cancelSupplierInvoice,
  confirmSupplierPayment,
  createSupplierInvoiceFromOrder,
  createSupplierPayment,
  listBankAccounts,
  listCashSessions,
  listSupplierInvoices,
  listSupplierPayments,
  validateSupplierInvoice,
  type PaymentMethod,
} from '../api/finance'
import { listPartners } from '../api/partners'
import { listPurchaseOrders } from '../api/purchases'
import { useAuth } from '../auth/AuthContext'

export default function SupplierInvoicesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManageInvoices = hasRole('comptable', 'achats')
  const canManagePayments = hasRole('caissier', 'comptable')

  const { data: invoices } = useQuery({ queryKey: ['supplier-invoices'], queryFn: listSupplierInvoices })
  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const { data: payments } = useQuery({ queryKey: ['supplier-payments'], queryFn: listSupplierPayments })
  const { data: orders } = useQuery({ queryKey: ['purchase-orders'], queryFn: listPurchaseOrders })
  const { data: cashSessions } = useQuery({ queryKey: ['cash-sessions'], queryFn: listCashSessions })
  const { data: bankAccounts } = useQuery({ queryKey: ['bank-accounts'], queryFn: listBankAccounts })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['supplier-invoices'] })
    queryClient.invalidateQueries({ queryKey: ['supplier-payments'] })
    queryClient.invalidateQueries({ queryKey: ['cash-sessions'] })
    queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
  }
  const createFromOrderMutation = useMutation({ mutationFn: createSupplierInvoiceFromOrder, onSuccess: invalidate })
  const validateMutation = useMutation({ mutationFn: validateSupplierInvoice, onSuccess: invalidate })
  const cancelMutation = useMutation({ mutationFn: cancelSupplierInvoice, onSuccess: invalidate })
  const createPaymentMutation = useMutation({ mutationFn: createSupplierPayment, onSuccess: invalidate })
  const confirmPaymentMutation = useMutation({ mutationFn: confirmSupplierPayment, onSuccess: invalidate })

  const [pendingOrderId, setPendingOrderId] = useState('')
  const [paymentAmount, setPaymentAmount] = useState<Record<number, string>>({})
  const [paymentMethod, setPaymentMethod] = useState<Record<number, PaymentMethod>>({})
  const [paymentTarget, setPaymentTarget] = useState<Record<number, string>>({})

  const invoicedOrderIds = new Set(invoices?.map((i) => i.purchase_order_id).filter(Boolean))
  const invoiceableOrders = orders?.filter((o) => o.state === 'commande' && !invoicedOrderIds.has(o.id)) ?? []
  const openSessions = cashSessions?.filter((s) => s.state === 'open') ?? []

  function handleCreateFromOrder(e: FormEvent) {
    e.preventDefault()
    if (!pendingOrderId) return
    createFromOrderMutation.mutate(Number(pendingOrderId))
    setPendingOrderId('')
  }

  function handlePaymentSubmit(e: FormEvent, invoiceId: number) {
    e.preventDefault()
    const amount = Number(paymentAmount[invoiceId])
    const method = paymentMethod[invoiceId] ?? 'especes'
    const target = paymentTarget[invoiceId]
    if (!amount) return
    createPaymentMutation.mutate({
      invoice_id: invoiceId,
      amount,
      payment_date: new Date().toISOString().slice(0, 10),
      payment_method: method,
      cash_session_id: method === 'especes' && target ? Number(target) : undefined,
      bank_account_id: method === 'banque' && target ? Number(target) : undefined,
    })
    setPaymentAmount((prev) => ({ ...prev, [invoiceId]: '' }))
  }

  return (
    <div>
      <h1>Factures fournisseurs (dettes)</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Type</th>
            <th>Fournisseur</th>
            <th>Statut</th>
            <th>Total</th>
            <th>Paye</th>
            <th>Reste</th>
            <th>Paiement</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {invoices?.map((inv) => (
            <tr key={inv.id}>
              <td>{inv.reference}</td>
              <td>{inv.move_type === 'bill' ? 'Facture' : 'Avoir'}</td>
              <td>{partners?.find((p) => p.id === inv.supplier_id)?.name ?? inv.supplier_id}</td>
              <td>{inv.payment_state}</td>
              <td>{inv.amount_total}</td>
              <td>{inv.amount_paid}</td>
              <td>{inv.amount_due}</td>
              <td>
                {canManagePayments && inv.state === 'validated' && inv.payment_state !== 'paid' && (
                  <form onSubmit={(e) => handlePaymentSubmit(e, inv.id)} style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    <input
                      type="number"
                      placeholder="Montant"
                      style={{ width: 80 }}
                      value={paymentAmount[inv.id] ?? ''}
                      onChange={(e) => setPaymentAmount((prev) => ({ ...prev, [inv.id]: e.target.value }))}
                    />
                    <select
                      value={paymentMethod[inv.id] ?? 'especes'}
                      onChange={(e) => setPaymentMethod((prev) => ({ ...prev, [inv.id]: e.target.value as PaymentMethod }))}
                    >
                      <option value="especes">Especes</option>
                      <option value="banque">Banque</option>
                    </select>
                    <select
                      value={paymentTarget[inv.id] ?? ''}
                      onChange={(e) => setPaymentTarget((prev) => ({ ...prev, [inv.id]: e.target.value }))}
                    >
                      <option value="">
                        {(paymentMethod[inv.id] ?? 'especes') === 'especes' ? 'Session de caisse' : 'Compte bancaire'}
                      </option>
                      {(paymentMethod[inv.id] ?? 'especes') === 'especes'
                        ? openSessions.map((s) => (
                            <option key={s.id} value={s.id}>
                              Caisse #{s.register_id} (session {s.id})
                            </option>
                          ))
                        : bankAccounts?.map((a) => (
                            <option key={a.id} value={a.id}>
                              {a.name}
                            </option>
                          ))}
                    </select>
                    <button type="submit">Payer</button>
                  </form>
                )}
              </td>
              <td>
                {canManageInvoices && inv.state === 'draft' && (
                  <button onClick={() => validateMutation.mutate(inv.id)}>Valider</button>
                )}
                {canManageInvoices && inv.state !== 'cancelled' && inv.amount_paid === 0 && (
                  <button onClick={() => cancelMutation.mutate(inv.id)}>Annuler</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManageInvoices && (
        <form className="inline-form" onSubmit={handleCreateFromOrder}>
          <h2>Facturer une commande d'achat</h2>
          <select value={pendingOrderId} onChange={(e) => setPendingOrderId(e.target.value)} required>
            <option value="">Commande confirmee</option>
            {invoiceableOrders.map((o) => (
              <option key={o.id} value={o.id}>
                {o.reference}
              </option>
            ))}
          </select>
          <button type="submit" disabled={createFromOrderMutation.isPending}>
            Creer la facture
          </button>
        </form>
      )}

      <h2>Paiements fournisseurs en attente de confirmation</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Facture</th>
            <th>Montant</th>
            <th>Mode</th>
            <th>Statut</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {payments
            ?.filter((p) => p.state === 'draft')
            .map((p) => (
              <tr key={p.id}>
                <td>{p.reference}</td>
                <td>{invoices?.find((i) => i.id === p.invoice_id)?.reference ?? p.invoice_id}</td>
                <td>{p.amount}</td>
                <td>{p.payment_method}</td>
                <td>{p.state}</td>
                <td>
                  {canManagePayments && (
                    <button onClick={() => confirmPaymentMutation.mutate(p.id)}>Confirmer</button>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
