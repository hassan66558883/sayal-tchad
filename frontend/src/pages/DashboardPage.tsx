import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  Banknote,
  FilePlus,
  Package,
  Receipt,
  ShoppingCart,
  Truck,
  UserPlus,
  UsersRound,
  Wallet,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboardSummary } from '../api/dashboard'
import { useAuth } from '../auth/AuthContext'

function firstOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
}

function lastOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)
}

const currencyFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })

function fcfa(value: number): string {
  return `${currencyFormatter.format(value)} FCFA`
}

function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function KpiCard({
  icon,
  tone,
  value,
  label,
}: {
  icon: React.ReactNode
  tone?: 'gold' | 'success' | 'warning'
  value: string
  label: string
}) {
  return (
    <div className="kpi-card">
      <div className="kpi-top">
        <span className={`kpi-icon ${tone ?? ''}`}>{icon}</span>
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [periodStart, setPeriodStart] = useState(firstOfMonth())
  const [periodEnd, setPeriodEnd] = useState(lastOfMonth())

  const { data } = useQuery({
    queryKey: ['dashboard-summary', periodStart, periodEnd],
    queryFn: () => getDashboardSummary(periodStart, periodEnd),
  })

  return (
    <div>
      <h1>Bonjour, {user?.name ?? ''}</h1>
      <p className="page-subtitle">Voici un apercu de l'activite de SAYAL sur la periode selectionnee.</p>

      <div className="quick-actions">
        <Link to="/sale-orders">
          <FilePlus size={15} /> Nouveau devis
        </Link>
        <Link to="/purchase-orders">
          <ShoppingCart size={15} /> Nouvelle commande d'achat
        </Link>
        <Link to="/partners">
          <UserPlus size={15} /> Nouveau client
        </Link>
        <Link to="/delivery-routes">
          <Truck size={15} /> Nouvelle tournee
        </Link>
        <Link to="/invoices">
          <Wallet size={15} /> Encaissement
        </Link>
        <Link to="/stock-moves">
          <Package size={15} /> Entree stock
        </Link>
      </div>

      <div className="inline-form" style={{ marginBottom: 20, flexDirection: 'row', alignItems: 'flex-end', gap: 16 }}>
        <label>
          Du
          <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
        </label>
        <label>
          Au
          <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
        </label>
      </div>

      {!data ? (
        <p>Chargement...</p>
      ) : (
        <>
          <div className="kpi-grid">
            <KpiCard
              icon={<Receipt size={18} />}
              value={fcfa(data.sales.total_invoiced)}
              label="Chiffre d'affaires facture"
            />
            <KpiCard
              icon={<ShoppingCart size={18} />}
              tone="gold"
              value={fcfa(data.sales.total_confirmed_sales)}
              label="Commandes confirmees"
            />
            <KpiCard icon={<Wallet size={18} />} tone="success" value={fcfa(data.sales.total_collected)} label="Encaisse" />
            <KpiCard
              icon={<AlertTriangle size={18} />}
              tone="warning"
              value={fcfa(data.finance.total_receivables)}
              label="Creances clients"
            />
            <KpiCard
              icon={<Receipt size={18} />}
              tone="warning"
              value={fcfa(data.finance.total_payables)}
              label="Dettes fournisseurs"
            />
            <KpiCard
              icon={<Banknote size={18} />}
              tone="success"
              value={fcfa(
                data.finance.cash_sessions.reduce((sum, s) => sum + s.balance, 0) +
                  data.finance.bank_accounts.reduce((sum, a) => sum + a.balance, 0),
              )}
              label="Solde caisse + banque"
            />
            <KpiCard icon={<UsersRound size={18} />} value={String(data.hr.active_employee_count)} label="Employes actifs" />
            <KpiCard
              icon={<Truck size={18} />}
              tone="gold"
              value={String(data.distribution.open_delivery_routes)}
              label="Tournees en cours"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
            <div className="panel">
              <h2>Ressources humaines</h2>
              <table className="data-table">
                <tbody>
                  <tr>
                    <td>En conge aujourd'hui</td>
                    <td>{data.hr.on_leave_today_count}</td>
                  </tr>
                  <tr>
                    <td>Demandes de conge en attente</td>
                    <td>{data.hr.pending_leave_requests}</td>
                  </tr>
                  <tr>
                    <td>Masse salariale (periode)</td>
                    <td>{fcfa(data.hr.payroll_cost)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="panel">
              <h2>Alertes stock bas</h2>
              {data.stock.low_stock_products.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>Aucune alerte.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Produit</th>
                      <th>Disponible</th>
                      <th>Seuil</th>
                      <th>Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.stock.low_stock_products.map((p) => (
                      <tr key={p.product_id}>
                        <td>{p.name}</td>
                        <td>{p.qty_on_hand}</td>
                        <td>{p.min_stock_qty}</td>
                        <td>
                          {p.qty_on_hand <= 0 ? (
                            <span className="badge badge-danger">
                              <XCircle size={12} /> Rupture
                            </span>
                          ) : (
                            <span className="badge badge-warning">
                              <AlertTriangle size={12} /> Stock faible
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="panel">
              <h2>Documents vehicule expirant sous 30 jours</h2>
              {data.fleet.expiring_documents.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>Aucun document expirant.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Vehicule</th>
                      <th>Type</th>
                      <th>Expiration</th>
                      <th>Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.fleet.expiring_documents.map((d, i) => (
                      <tr key={i}>
                        <td>{d.vehicle_id}</td>
                        <td>{d.document_type}</td>
                        <td>{d.end_date}</td>
                        <td>
                          {daysUntil(d.end_date) <= 7 ? (
                            <span className="badge badge-danger">Urgent</span>
                          ) : (
                            <span className="badge badge-warning">A surveiller</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
