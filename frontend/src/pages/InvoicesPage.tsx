import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listPartners } from '../api/partners'
import {
  cancelInvoice,
  confirmPayment,
  createPayment,
  listInvoices,
  listPayments,
  validateInvoice,
} from '../api/sales'
import { useAuth } from '../auth/AuthContext'

export default function InvoicesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManageInvoices = hasRole('ventes')
  const canManagePayments = hasRole('caissier', 'comptable')

  const { data: invoices } = useQuery({ queryKey: ['invoices'], queryFn: listInvoices })
  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const { data: payments } = useQuery({ queryKey: ['payments'], queryFn: listPayments })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] })
    queryClient.invalidateQueries({ queryKey: ['payments'] })
  }
  const validateMutation = useMutation({ mutationFn: validateInvoice, onSuccess: invalidate })
  const cancelMutation = useMutation({ mutationFn: cancelInvoice, onSuccess: invalidate })
  const createPaymentMutation = useMutation({ mutationFn: createPayment, onSuccess: invalidate })
  const confirmPaymentMutation = useMutation({ mutationFn: confirmPayment, onSuccess: invalidate })

  const [paymentAmount, setPaymentAmount] = useState<Record<number, string>>({})

  function handlePaymentSubmit(e: FormEvent, invoiceId: number) {
    e.preventDefault()
    const amount = Number(paymentAmount[invoiceId])
    if (!amount) return
    createPaymentMutation.mutate({
      invoice_id: invoiceId,
      amount,
      payment_date: new Date().toISOString().slice(0, 10),
    })
    setPaymentAmount((prev) => ({ ...prev, [invoiceId]: '' }))
  }

  return (
    <div>
      <h1>Factures</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Type</th>
            <th>Client</th>
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
              <td>{inv.move_type === 'invoice' ? 'Facture' : 'Avoir'}</td>
              <td>{partners?.find((p) => p.id === inv.customer_id)?.name ?? inv.customer_id}</td>
              <td>{inv.payment_state}</td>
              <td>{inv.amount_total}</td>
              <td>{inv.amount_paid}</td>
              <td>{inv.amount_due}</td>
              <td>
                {canManagePayments && inv.state === 'validated' && inv.payment_state !== 'paid' && (
                  <form onSubmit={(e) => handlePaymentSubmit(e, inv.id)} style={{ display: 'flex', gap: 4 }}>
                    <input
                      type="number"
                      placeholder="Montant"
                      style={{ width: 80 }}
                      value={paymentAmount[inv.id] ?? ''}
                      onChange={(e) => setPaymentAmount((prev) => ({ ...prev, [inv.id]: e.target.value }))}
                    />
                    <button type="submit">Encaisser</button>
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

      <h2>Paiements en attente de confirmation</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Facture</th>
            <th>Montant</th>
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
