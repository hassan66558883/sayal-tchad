import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { confirmDelivery, listDeliveries } from '../api/deliveries'
import { listProducts } from '../api/products'

export default function DeliveriesPage() {
  const queryClient = useQueryClient()
  const { data: deliveries } = useQuery({ queryKey: ['deliveries'], queryFn: listDeliveries })
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts })

  const confirmMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Parameters<typeof confirmDelivery>[1] }) =>
      confirmDelivery(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deliveries'] }),
  })

  const [qtyByLine, setQtyByLine] = useState<Record<number, string>>({})
  const [signatureByDelivery, setSignatureByDelivery] = useState<Record<number, string>>({})
  const [issueByDelivery, setIssueByDelivery] = useState<Record<number, string>>({})
  const [errorByDelivery, setErrorByDelivery] = useState<Record<number, string>>({})

  function productName(id: number) {
    return products?.find((p) => p.id === id)?.name ?? id
  }

  function submitConfirm(deliveryId: number, lineIds: number[]) {
    const lines = lineIds.map((lineId) => ({
      line_id: lineId,
      delivered_qty: Number(qtyByLine[lineId] ?? 0),
    }))
    confirmMutation.mutate(
      {
        id: deliveryId,
        input: {
          lines,
          signature_data: signatureByDelivery[deliveryId] || undefined,
          issue_description: issueByDelivery[deliveryId] || undefined,
        },
      },
      {
        onError: () =>
          setErrorByDelivery((prev) => ({ ...prev, [deliveryId]: 'Confirmation refusee (signature manquante ou quantite invalide).' })),
        onSuccess: () => setErrorByDelivery((prev) => ({ ...prev, [deliveryId]: '' })),
      },
    )
  }

  return (
    <div>
      <h1>Mes livraisons</h1>
      {deliveries?.map((d) => (
        <div key={d.id} className="inline-form" style={{ marginBottom: 16 }}>
          <h2>
            {d.reference} - {d.state}
          </h2>
          {d.lines.map((line) => (
            <div key={line.id}>
              {productName(line.product_id)} - commande : {line.ordered_qty}
              {['chargee', 'en_livraison'].includes(d.state) ? (
                <input
                  type="number"
                  placeholder="Quantite livree"
                  value={qtyByLine[line.id] ?? ''}
                  onChange={(e) => setQtyByLine((prev) => ({ ...prev, [line.id]: e.target.value }))}
                  style={{ marginLeft: 8, width: 100 }}
                />
              ) : (
                <span> - livree : {line.delivered_qty}</span>
              )}
            </div>
          ))}
          {['chargee', 'en_livraison'].includes(d.state) && (
            <>
              <input
                placeholder="Signature (texte, tient lieu de capture signature)"
                value={signatureByDelivery[d.id] ?? ''}
                onChange={(e) => setSignatureByDelivery((prev) => ({ ...prev, [d.id]: e.target.value }))}
              />
              <input
                placeholder="Probleme rencontre (optionnel)"
                value={issueByDelivery[d.id] ?? ''}
                onChange={(e) => setIssueByDelivery((prev) => ({ ...prev, [d.id]: e.target.value }))}
              />
              <button onClick={() => submitConfirm(d.id, d.lines.map((l) => l.id))}>Confirmer la livraison</button>
              {errorByDelivery[d.id] && <p className="error">{errorByDelivery[d.id]}</p>}
            </>
          )}
          {d.state === 'probleme' && d.issue_description && <p className="error">Probleme : {d.issue_description}</p>}
        </div>
      ))}
      {deliveries?.length === 0 && <p>Aucune livraison assignee.</p>}
    </div>
  )
}
