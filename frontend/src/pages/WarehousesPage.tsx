import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { listProducts } from '../api/products'
import { createWarehouse, getProductStock, getWarehouseSummary, listWarehouses } from '../api/stock'
import { useAuth } from '../auth/AuthContext'

function thirtyDaysAgo(): string {
  const d = new Date()
  d.setDate(d.getDate() - 29)
  return d.toISOString().slice(0, 10)
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function WarehousesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('stock')

  const { data: warehouses } = useQuery({ queryKey: ['warehouses'], queryFn: listWarehouses })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })

  const periodStart = thirtyDaysAgo()
  const periodEnd = today()
  const summaryQueries = useQueries({
    queries: (warehouses ?? []).map((w) => ({
      queryKey: ['warehouse-summary', w.id, periodStart, periodEnd],
      queryFn: () => getWarehouseSummary(w.id, periodStart, periodEnd),
    })),
  })
  const summaryByWarehouse = new Map((warehouses ?? []).map((w, i) => [w.id, summaryQueries[i]?.data]))

  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const mutation = useMutation({
    mutationFn: createWarehouse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      setName('')
      setCode('')
    },
  })

  const [selectedProductId, setSelectedProductId] = useState('')
  const { data: stock } = useQuery({
    queryKey: ['product-stock', selectedProductId],
    queryFn: () => getProductStock(Number(selectedProductId)),
    enabled: !!selectedProductId,
  })

  return (
    <div>
      <h1>Entrepots</h1>
      <p className="page-subtitle">Stock actuel et mouvements des 30 derniers jours, par entrepot.</p>
      <table className="data-table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Nom</th>
            <th>Stock actuel</th>
            <th>Entrees (30j)</th>
            <th>Sorties (30j)</th>
            <th>Transferts recus (30j)</th>
          </tr>
        </thead>
        <tbody>
          {warehouses?.map((w) => {
            const s = summaryByWarehouse.get(w.id)
            return (
              <tr key={w.id}>
                <td>{w.code}</td>
                <td>{w.name}</td>
                <td>{s ? s.current_qty : '...'}</td>
                <td>{s ? s.incoming_qty : '...'}</td>
                <td>{s ? s.outgoing_qty : '...'}</td>
                <td>{s ? s.transfers_qty : '...'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {canManage && (
        <form
          className="inline-form"
          onSubmit={(e: FormEvent) => {
            e.preventDefault()
            mutation.mutate({ name, code })
          }}
        >
          <h2>Nouvel entrepot</h2>
          <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
          <input placeholder="Code" value={code} onChange={(e) => setCode(e.target.value)} required />
          <button type="submit">Creer</button>
        </form>
      )}

      <div className="inline-form" style={{ marginTop: 24 }}>
        <h2>Stock disponible / en transit</h2>
        <select value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
          <option value="">Choisir un produit</option>
          {products?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {stock && (
          <p>
            Stock disponible : <strong>{stock.qty_on_hand}</strong> - En transit :{' '}
            <strong>{stock.qty_in_transit}</strong>
          </p>
        )}
      </div>
    </div>
  )
}
