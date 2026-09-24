import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listPartners } from '../api/partners'
import { listProducts } from '../api/products'
import {
  cancelPurchaseOrder,
  confirmPurchaseOrder,
  createPurchaseOrder,
  listPurchaseOrders,
  terminatePurchaseOrder,
} from '../api/purchases'
import { useAuth } from '../auth/AuthContext'

interface DraftLine {
  product_id: number
  qty: number
  unit_price: number
}

export default function PurchaseOrdersPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('achats')

  const { data: orders } = useQuery({ queryKey: ['purchase-orders'], queryFn: listPurchaseOrders })
  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })
  const suppliers = partners?.filter((p) => p.is_supplier) ?? []

  const [supplierId, setSupplierId] = useState('')
  const [orderDate, setOrderDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [lines, setLines] = useState<DraftLine[]>([])
  const [lineProductId, setLineProductId] = useState('')
  const [lineQty, setLineQty] = useState('')
  const [linePrice, setLinePrice] = useState('')
  const [error, setError] = useState<string | null>(null)

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
  const createMutation = useMutation({
    mutationFn: createPurchaseOrder,
    onSuccess: () => {
      invalidate()
      setLines([])
      setSupplierId('')
      setError(null)
    },
    onError: () => setError('Impossible de creer la commande.'),
  })
  const confirmMutation = useMutation({ mutationFn: confirmPurchaseOrder, onSuccess: invalidate })
  const terminateMutation = useMutation({ mutationFn: terminatePurchaseOrder, onSuccess: invalidate })
  const cancelMutation = useMutation({ mutationFn: cancelPurchaseOrder, onSuccess: invalidate })

  function addLine() {
    if (!lineProductId || !lineQty || !linePrice) return
    setLines((prev) => [
      ...prev,
      { product_id: Number(lineProductId), qty: Number(lineQty), unit_price: Number(linePrice) },
    ])
    setLineProductId('')
    setLineQty('')
    setLinePrice('')
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate({ supplier_id: Number(supplierId), order_date: orderDate, lines })
  }

  function productName(id: number) {
    return products?.find((p) => p.id === id)?.name ?? id
  }

  return (
    <div>
      <h1>Commandes d'achat</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Fournisseur</th>
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
              <td>{partners?.find((p) => p.id === o.supplier_id)?.name ?? o.supplier_id}</td>
              <td>{o.order_date}</td>
              <td>{o.state}</td>
              <td>{o.amount_total}</td>
              <td>
                {canManage && o.state === 'proforma' && (
                  <button onClick={() => confirmMutation.mutate(o.id)}>Confirmer</button>
                )}
                {canManage && o.state === 'commande' && (
                  <button onClick={() => terminateMutation.mutate(o.id)}>Terminer</button>
                )}
                {canManage && (o.state === 'proforma' || o.state === 'commande') && (
                  <button onClick={() => cancelMutation.mutate(o.id)}>Annuler</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit} style={{ maxWidth: 520 }}>
          <h2>Nouvelle commande</h2>
          <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
            <option value="">Fournisseur</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input type="date" value={orderDate} onChange={(e) => setOrderDate(e.target.value)} required />

          <fieldset className="role-picker">
            <legend>Lignes</legend>
            {lines.map((l, i) => (
              <div key={i}>
                {productName(l.product_id)} x {l.qty} @ {l.unit_price}
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
            <button type="button" onClick={addLine}>
              Ajouter la ligne
            </button>
          </fieldset>

          <button type="submit" disabled={createMutation.isPending || lines.length === 0}>
            Creer la commande
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  )
}
