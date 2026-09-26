import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { CUSTOMER_TYPES, createPartner, listPartners } from '../api/partners'
import { getSupplierBalance } from '../api/finance'
import { getPartnerBalance } from '../api/sales'
import { useAuth } from '../auth/AuthContext'

export default function PartnersPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const canManage = hasRole('ventes', 'achats')

  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const customerIds = partners?.filter((p) => p.is_customer).map((p) => p.id) ?? []
  const balanceQueries = useQueries({
    queries: customerIds.map((id) => ({
      queryKey: ['partner-balance', id],
      queryFn: () => getPartnerBalance(id),
    })),
  })
  const balanceById = new Map(customerIds.map((id, i) => [id, balanceQueries[i]?.data?.balance]))

  const supplierIds = partners?.filter((p) => p.is_supplier).map((p) => p.id) ?? []
  const supplierBalanceQueries = useQueries({
    queries: supplierIds.map((id) => ({
      queryKey: ['supplier-balance', id],
      queryFn: () => getSupplierBalance(id),
    })),
  })
  const supplierBalanceById = new Map(supplierIds.map((id, i) => [id, supplierBalanceQueries[i]?.data?.balance]))

  const [name, setName] = useState('')
  const [isCustomer, setIsCustomer] = useState(true)
  const [isSupplier, setIsSupplier] = useState(false)
  const [customerType, setCustomerType] = useState('')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: createPartner,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners'] })
      setName('')
      setPhone('')
      setError(null)
    },
    onError: () => setError('Impossible de creer ce tiers.'),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate({
      name,
      is_customer: isCustomer,
      is_supplier: isSupplier,
      customer_type: isCustomer && customerType ? customerType : undefined,
      phone: phone || undefined,
    })
  }

  return (
    <div>
      <h1>Clients &amp; Fournisseurs</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reference</th>
            <th>Nom</th>
            <th>Type</th>
            <th>Telephone</th>
            <th>Solde client</th>
            <th>Solde fournisseur (dette)</th>
          </tr>
        </thead>
        <tbody>
          {partners?.map((p) => (
            <tr key={p.id}>
              <td>{p.reference}</td>
              <td>{p.name}</td>
              <td>
                {[p.is_customer && 'Client', p.is_supplier && 'Fournisseur'].filter(Boolean).join(' / ')}
              </td>
              <td>{p.phone ?? '-'}</td>
              <td>{p.is_customer ? (balanceById.get(p.id) ?? '...') : '-'}</td>
              <td>{p.is_supplier ? (supplierBalanceById.get(p.id) ?? '...') : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {canManage && (
        <form className="inline-form" onSubmit={handleSubmit}>
          <h2>Nouveau tiers</h2>
          <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
          <label>
            <input type="checkbox" checked={isCustomer} onChange={(e) => setIsCustomer(e.target.checked)} />
            Client
          </label>
          <label>
            <input type="checkbox" checked={isSupplier} onChange={(e) => setIsSupplier(e.target.checked)} />
            Fournisseur
          </label>
          {isCustomer && (
            <select value={customerType} onChange={(e) => setCustomerType(e.target.value)}>
              <option value="">Type de client (optionnel)</option>
              {CUSTOMER_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}
          <input placeholder="Telephone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <button type="submit" disabled={mutation.isPending}>
            Creer
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  )
}
