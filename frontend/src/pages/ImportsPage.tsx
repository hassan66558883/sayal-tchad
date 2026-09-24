import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import {
  advanceImport,
  createContainer,
  createImport,
  listContainers,
  listImports,
  listPurchaseOrders,
  updateImportCosts,
} from '../api/purchases'
import { useAuth } from '../auth/AuthContext'

const NEXT_LABEL: Record<string, string> = {
  nouveau: 'Marquer expedie',
  expedie: 'Marquer arrive',
  arrive: 'Passer en douane',
  douane: 'Marquer receptionne',
}

export default function ImportsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('achats')

  const { data: imports } = useQuery({ queryKey: ['imports'], queryFn: listImports })
  const { data: orders } = useQuery({ queryKey: ['purchase-orders'], queryFn: listPurchaseOrders })
  const { data: containers } = useQuery({ queryKey: ['containers'], queryFn: listContainers })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['imports'] })
    queryClient.invalidateQueries({ queryKey: ['products'] })
  }
  const createMutation = useMutation({ mutationFn: createImport, onSuccess: invalidate })
  const advanceMutation = useMutation({ mutationFn: advanceImport, onSuccess: invalidate })
  const costsMutation = useMutation({
    mutationFn: ({ id, ...rest }: { id: number; transport_cost: number; customs_cost: number; transit_cost: number; other_costs: number }) =>
      updateImportCosts(id, rest),
    onSuccess: invalidate,
  })

  const [orderId, setOrderId] = useState('')
  const [containerId, setContainerId] = useState('')
  const importedOrderIds = new Set(imports?.map((i) => i.purchase_order_id))
  const eligibleOrders = orders?.filter((o) => o.state === 'commande' && !importedOrderIds.has(o.id)) ?? []

  const [containerNumber, setContainerNumber] = useState('')
  const containerMutation = useMutation({
    mutationFn: createContainer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['containers'] })
      setContainerNumber('')
    },
  })

  function handleCreateImport(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate({
      purchase_order_id: Number(orderId),
      container_id: containerId ? Number(containerId) : undefined,
    })
    setOrderId('')
  }

  function handleCostsSubmit(e: FormEvent<HTMLFormElement>, id: number) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    costsMutation.mutate({
      id,
      transport_cost: Number(form.get('transport_cost') || 0),
      customs_cost: Number(form.get('customs_cost') || 0),
      transit_cost: Number(form.get('transit_cost') || 0),
      other_costs: Number(form.get('other_costs') || 0),
    })
  }

  return (
    <div>
      <h1>Importations</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Commande</th>
            <th>Statut</th>
            <th>Frais (transport/douane/transit/autres)</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {imports?.map((imp) => {
            const order = orders?.find((o) => o.id === imp.purchase_order_id)
            return (
              <tr key={imp.id}>
                <td>{imp.reference}</td>
                <td>{order?.reference ?? imp.purchase_order_id}</td>
                <td>{imp.state}</td>
                <td>
                  {imp.state === 'receptionne' ? (
                    `${imp.transport_cost} / ${imp.customs_cost} / ${imp.transit_cost} / ${imp.other_costs}`
                  ) : canManage ? (
                    <form onSubmit={(e) => handleCostsSubmit(e, imp.id)} style={{ display: 'flex', gap: 4 }}>
                      <input name="transport_cost" type="number" defaultValue={imp.transport_cost} style={{ width: 70 }} />
                      <input name="customs_cost" type="number" defaultValue={imp.customs_cost} style={{ width: 70 }} />
                      <input name="transit_cost" type="number" defaultValue={imp.transit_cost} style={{ width: 70 }} />
                      <input name="other_costs" type="number" defaultValue={imp.other_costs} style={{ width: 70 }} />
                      <button type="submit">Sauver</button>
                    </form>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  {canManage && imp.state !== 'receptionne' && (
                    <button onClick={() => advanceMutation.mutate(imp.id)}>{NEXT_LABEL[imp.state]}</button>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {canManage && (
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <form className="inline-form" onSubmit={handleCreateImport}>
            <h2>Nouvelle importation</h2>
            <select value={orderId} onChange={(e) => setOrderId(e.target.value)} required>
              <option value="">Commande confirmee</option>
              {eligibleOrders.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.reference}
                </option>
              ))}
            </select>
            <select value={containerId} onChange={(e) => setContainerId(e.target.value)}>
              <option value="">Conteneur (optionnel)</option>
              {containers?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.number}
                </option>
              ))}
            </select>
            <button type="submit" disabled={createMutation.isPending}>
              Creer
            </button>
          </form>

          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault()
              containerMutation.mutate({ number: containerNumber })
            }}
          >
            <h2>Nouveau conteneur</h2>
            <input
              placeholder="Numero"
              value={containerNumber}
              onChange={(e) => setContainerNumber(e.target.value)}
              required
            />
            <button type="submit">Creer</button>
          </form>
        </div>
      )}
    </div>
  )
}
