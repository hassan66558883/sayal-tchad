import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { getSupplierBalance } from '../api/finance'
import { listPartners } from '../api/partners'
import { listDeliveries } from '../api/deliveries'
import { listInvoices, listSaleOrders, getPartnerBalance } from '../api/sales'
import StatusBadge from '../components/StatusBadge'

const currencyFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
function fcfa(value: number): string {
  return `${currencyFormatter.format(value)} FCFA`
}

type Tab = 'apercu' | 'commandes' | 'factures' | 'livraisons'

export default function PartnerDetailPage() {
  const { id } = useParams()
  const partnerId = Number(id)
  const [tab, setTab] = useState<Tab>('apercu')

  const { data: partners } = useQuery({ queryKey: ['partners'], queryFn: listPartners })
  const partner = partners?.find((p) => p.id === partnerId)

  const { data: orders } = useQuery({ queryKey: ['sale-orders'], queryFn: listSaleOrders })
  const { data: invoices } = useQuery({ queryKey: ['invoices'], queryFn: listInvoices })
  const { data: deliveries } = useQuery({ queryKey: ['deliveries'], queryFn: listDeliveries })

  const { data: balance } = useQuery({
    queryKey: ['partner-balance', partnerId],
    queryFn: () => getPartnerBalance(partnerId),
    enabled: !!partner?.is_customer,
  })
  const { data: supplierBalance } = useQuery({
    queryKey: ['supplier-balance', partnerId],
    queryFn: () => getSupplierBalance(partnerId),
    enabled: !!partner?.is_supplier,
  })

  const partnerOrders = orders?.filter((o) => o.customer_id === partnerId) ?? []
  const partnerOrderIds = new Set(partnerOrders.map((o) => o.id))
  const partnerInvoices = invoices?.filter((i) => i.customer_id === partnerId) ?? []
  const partnerDeliveries = deliveries?.filter((d) => d.sale_order_id && partnerOrderIds.has(d.sale_order_id)) ?? []

  if (!partner) {
    return <p>Chargement...</p>
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'apercu', label: 'Apercu' },
    { key: 'commandes', label: `Commandes (${partnerOrders.length})` },
    { key: 'factures', label: `Factures (${partnerInvoices.length})` },
    { key: 'livraisons', label: `Livraisons (${partnerDeliveries.length})` },
  ]

  return (
    <div>
      <h1>{partner.name}</h1>
      <p className="page-subtitle">
        {partner.reference}
        {partner.is_customer && <span className="badge badge-gold" style={{ marginLeft: 8 }}>Client</span>}
        {partner.is_supplier && <span className="badge badge-muted" style={{ marginLeft: 8 }}>Fournisseur</span>}
      </p>

      <div className="quick-actions" style={{ marginBottom: 20 }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              border: '1px solid var(--border)',
              background: tab === t.key ? 'var(--accent)' : 'var(--panel-bg)',
              color: tab === t.key ? '#fff' : 'var(--text)',
              borderRadius: 999,
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'apercu' && (
        <div className="kpi-grid">
          {partner.is_customer && (
            <div className="kpi-card">
              <div className="kpi-value">{balance !== undefined ? fcfa(balance.balance) : '...'}</div>
              <div className="kpi-label">Solde client (creances)</div>
            </div>
          )}
          {partner.is_supplier && (
            <div className="kpi-card">
              <div className="kpi-value">{supplierBalance !== undefined ? fcfa(supplierBalance.balance) : '...'}</div>
              <div className="kpi-label">Solde fournisseur (dettes)</div>
            </div>
          )}
          <div className="kpi-card">
            <div className="kpi-value">{partner.phone ?? '-'}</div>
            <div className="kpi-label">Telephone</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{partner.email ?? '-'}</div>
            <div className="kpi-label">Email</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{partner.address ?? '-'}</div>
            <div className="kpi-label">Adresse</div>
          </div>
          {partner.customer_type && (
            <div className="kpi-card">
              <div className="kpi-value">{partner.customer_type}</div>
              <div className="kpi-label">Type de client</div>
            </div>
          )}
        </div>
      )}

      {tab === 'commandes' && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Reference</th>
              <th>Date</th>
              <th>Statut</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {partnerOrders.map((o) => (
              <tr key={o.id}>
                <td>{o.reference}</td>
                <td>{o.order_date}</td>
                <td>
                  <StatusBadge status={o.state} />
                </td>
                <td>{fcfa(o.amount_total)}</td>
              </tr>
            ))}
            {partnerOrders.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: 'var(--text-muted)' }}>
                  Aucune commande.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {tab === 'factures' && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Reference</th>
              <th>Date</th>
              <th>Statut paiement</th>
              <th>Total</th>
              <th>Reste</th>
            </tr>
          </thead>
          <tbody>
            {partnerInvoices.map((i) => (
              <tr key={i.id}>
                <td>{i.reference}</td>
                <td>{i.invoice_date}</td>
                <td>
                  <StatusBadge status={i.payment_state} />
                </td>
                <td>{fcfa(i.amount_total)}</td>
                <td>{fcfa(i.amount_due)}</td>
              </tr>
            ))}
            {partnerInvoices.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: 'var(--text-muted)' }}>
                  Aucune facture.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {tab === 'livraisons' && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Reference</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {partnerDeliveries.map((d) => (
              <tr key={d.id}>
                <td>{d.reference}</td>
                <td>
                  <StatusBadge status={d.state} />
                </td>
              </tr>
            ))}
            {partnerDeliveries.length === 0 && (
              <tr>
                <td colSpan={2} style={{ color: 'var(--text-muted)' }}>
                  Aucune livraison.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
