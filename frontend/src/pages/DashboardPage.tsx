import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getDashboardSummary } from '../api/dashboard'

function firstOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
}

function lastOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)
}

export default function DashboardPage() {
  const [periodStart, setPeriodStart] = useState(firstOfMonth())
  const [periodEnd, setPeriodEnd] = useState(lastOfMonth())

  const { data } = useQuery({
    queryKey: ['dashboard-summary', periodStart, periodEnd],
    queryFn: () => getDashboardSummary(periodStart, periodEnd),
  })

  return (
    <div>
      <h1>Tableau de bord Direction</h1>
      <div className="inline-form" style={{ marginBottom: 16 }}>
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          <div className="data-table">
            <h2>Ventes</h2>
            <table className="data-table">
              <tbody>
                <tr>
                  <td>Commandes confirmees</td>
                  <td>{data.sales.total_confirmed_sales}</td>
                </tr>
                <tr>
                  <td>Facture (net avoirs)</td>
                  <td>{data.sales.total_invoiced}</td>
                </tr>
                <tr>
                  <td>Encaisse</td>
                  <td>{data.sales.total_collected}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="data-table">
            <h2>Finance</h2>
            <table className="data-table">
              <tbody>
                <tr>
                  <td>Creances clients</td>
                  <td>{data.finance.total_receivables}</td>
                </tr>
                <tr>
                  <td>Dettes fournisseurs</td>
                  <td>{data.finance.total_payables}</td>
                </tr>
                <tr>
                  <td>Sessions de caisse ouvertes</td>
                  <td>{data.finance.cash_sessions.length}</td>
                </tr>
                <tr>
                  <td>Solde caisse total</td>
                  <td>{data.finance.cash_sessions.reduce((sum, s) => sum + s.balance, 0)}</td>
                </tr>
                <tr>
                  <td>Solde bancaire total</td>
                  <td>{data.finance.bank_accounts.reduce((sum, a) => sum + a.balance, 0)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="data-table">
            <h2>Ressources humaines</h2>
            <table className="data-table">
              <tbody>
                <tr>
                  <td>Employes actifs</td>
                  <td>{data.hr.active_employee_count}</td>
                </tr>
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
                  <td>{data.hr.payroll_cost}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="data-table">
            <h2>Distribution</h2>
            <table className="data-table">
              <tbody>
                <tr>
                  <td>Tournees en cours</td>
                  <td>{data.distribution.open_delivery_routes}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="data-table">
            <h2>Alertes stock bas</h2>
            {data.stock.low_stock_products.length === 0 ? (
              <p>Aucune alerte.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Produit</th>
                    <th>Disponible</th>
                    <th>Seuil</th>
                  </tr>
                </thead>
                <tbody>
                  {data.stock.low_stock_products.map((p) => (
                    <tr key={p.product_id}>
                      <td>{p.name}</td>
                      <td>{p.qty_on_hand}</td>
                      <td>{p.min_stock_qty}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="data-table">
            <h2>Documents vehicule expirant sous 30 jours</h2>
            {data.fleet.expiring_documents.length === 0 ? (
              <p>Aucun document expirant.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Vehicule</th>
                    <th>Type</th>
                    <th>Expiration</th>
                  </tr>
                </thead>
                <tbody>
                  {data.fleet.expiring_documents.map((d, i) => (
                    <tr key={i}>
                      <td>{d.vehicle_id}</td>
                      <td>{d.document_type}</td>
                      <td>{d.end_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
