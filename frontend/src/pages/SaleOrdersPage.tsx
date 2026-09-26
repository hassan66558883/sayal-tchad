import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listPartners } from '../api/partners'
import { listProducts } from '../api/products'
import {
  cancelSaleOrder,
  confirmSaleOrder,
  createInvoiceFromOrder,
  createSaleOrder,
  listSaleOrders,
  terminateSaleOrder,
} from '../api/sales'
import { useAuth } from '../auth/AuthContext'

interface DraftLine {
  product_id: number
  qty: number
  unit_price: number
  discount_percent: number
}

export default function SaleOrdersPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('ventes')

  const { data: orders } = useQuery({ queryKey: ['sale-orders'], queryFn: listSaleOrders })
  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })
  const customers = partners?.filter((p) => p.is_customer) ?? []

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['sale-orders'] })
    queryClient.invalidateQueries({ queryKey: ['invoices'] })
  }
  const createMutation = useMutation({ mutationFn: createSaleOrder, onSuccess: invalidate })
  const confirmMutation = useMutation({
    mutationFn: confirmSaleOrder,
    onSuccess: invalidate,
    onError: () => setActionError('Confirmation refusee (limite de credit depassee ?).'),
  })
  const terminateMutation = useMutation({ mutationFn: terminateSaleOrder, onSuccess: invalidate })
  const cancelMutation = useMutation({ mutationFn: cancelSaleOrder, onSuccess: invalidate })
  const invoiceMutation = useMutation({ mutationFn: createInvoiceFromOrder, onSuccess: invalidate })

  const [customerId, setCustomerId] = useState('')
  const [orderDate, setOrderDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [lines, setLines] = useState<DraftLine[]>([])
  const [lineProductId, setLineProductId] = useState('')
  const [lineQty, setLineQty] = useState('')
  const [linePrice, setLinePrice] = useState('')
  const [lineDiscount, setLineDiscount] = useState('0')
  const [actionError, setActionError] = useState<string | null>(null)

  function addLine() {
    if (!lineProductId || !lineQty || !linePrice) return
    setLines((prev) => [
      ...prev,
      {
        product_id: Number(lineProductId),
        qty: Number(lineQty),
        unit_price: Number(linePrice),
        discount_percent: Number(lineDiscount || 0),
      },
    ])
    setLineProductId('')
    setLineQty('')
    setLinePrice('')
    setLineDiscount('0')
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate({ customer_id: Number(customerId), order_date: orderDate, lines })
    setLines([])
    setCustomerId('')
  }

  function productName(id: number) {
    return products?.find((p) => p.id === id)?.name ?? id
  }

  return (
    <div>
      <h1>Devis &amp; commandes</h1>
      {actionError && <p className="error">{actionError}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Client</th>
            <th>Date</th>
            <th>Statut</th>
            <th>Total</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {orders?.map((o) => (
            <tr key={o.id}>
              <td>{o.reference}</td>
              <td>{partners?.find((p) => p.id === o.customer_id)?.name ?? o.customer_id}</td>
              <td>{o.order_date}</td>
              <td>{o.state}</td>
              <td>{o.amount_total}</td>
              <td>
                {canManage && o.state === 'devis' && (
                  <button onClick={() => confirmMutation.mutate(o.id)}>Confirmer</button>
                )}
                {canManage && o.state === 'commande' && (
                  <>
                    <button onClick={() => invoiceMutation.mutate(o.id)}>Facturer</button>
                    <button onClick={() => terminateMutation.mutate(o.id)}>Terminer</button>
                  </>
                )}
                {canManage && (o.state === 'devis' || o.state === 'commande') && (
                  <button onClick={() => cancelMutation.mutate(o.id)}>Annuler</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit} style={{ maxWidth: 520 }}>
          <h2>Nouveau devis</h2>
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
            <option value="">Client</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <input type="date" value={orderDate} onChange={(e) => setOrderDate(e.target.value)} required />

          <fieldset className="role-picker">
            <legend>Lignes</legend>
            {lines.map((l, i) => (
              <div key={i}>
                {productName(l.product_id)} x {l.qty} @ {l.unit_price} (-{l.discount_percent}%)
              </div>
            ))}
            <select value={lineProductId} onChange={(e) => setLineProductId(e.target.value)}>
              <option value="">Produit</option>
              {products?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input placeholder="Quantite" type="number" value={lineQty} onChange={(e) => setLineQty(e.target.value)} />
            <input
              placeholder="Prix unitaire"
              type="number"
              value={linePrice}
              onChange={(e) => setLinePrice(e.target.value)}
            />
            <input
              placeholder="Remise %"
              type="number"
              value={lineDiscount}
              onChange={(e) => setLineDiscount(e.target.value)}
            />
            <button type="button" onClick={addLine}>
              Ajouter la ligne
            </button>
          </fieldset>

          <button type="submit" disabled={createMutation.isPending || lines.length === 0}>
            Creer le devis
          </button>
        </form>
      )}
    </div>
  )
}
