import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './auth/AuthContext'
import AuditLogsPage from './pages/AuditLogsPage'
import BankAccountsPage from './pages/BankAccountsPage'
import BranchesPage from './pages/BranchesPage'
import CashRegistersPage from './pages/CashRegistersPage'
import CommercialPage from './pages/CommercialPage'
import DeliveriesPage from './pages/DeliveriesPage'
import DeliveryRoutesPage from './pages/DeliveryRoutesPage'
import FleetOperationsPage from './pages/FleetOperationsPage'
import FleetPage from './pages/FleetPage'
import HRPage from './pages/HRPage'
import ImportsPage from './pages/ImportsPage'
import InvoicesPage from './pages/InvoicesPage'
import LoginPage from './pages/LoginPage'
import PartnersPage from './pages/PartnersPage'
import ProductsPage from './pages/ProductsPage'
import PurchaseOrdersPage from './pages/PurchaseOrdersPage'
import ReportsPage from './pages/ReportsPage'
import SaleOrdersPage from './pages/SaleOrdersPage'
import StockInventoriesPage from './pages/StockInventoriesPage'
import StockMovesPage from './pages/StockMovesPage'
import SupplierInvoicesPage from './pages/SupplierInvoicesPage'
import UsersPage from './pages/UsersPage'
import WarehousesPage from './pages/WarehousesPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<BranchesPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="partners" element={<PartnersPage />} />
              <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
              <Route path="imports" element={<ImportsPage />} />
              <Route path="warehouses" element={<WarehousesPage />} />
              <Route path="stock-moves" element={<StockMovesPage />} />
              <Route path="stock-inventories" element={<StockInventoriesPage />} />
              <Route path="sale-orders" element={<SaleOrdersPage />} />
              <Route path="invoices" element={<InvoicesPage />} />
              <Route path="commercial" element={<CommercialPage />} />
              <Route path="fleet" element={<FleetPage />} />
              <Route path="fleet-operations" element={<FleetOperationsPage />} />
              <Route path="delivery-routes" element={<DeliveryRoutesPage />} />
              <Route path="deliveries" element={<DeliveriesPage />} />
              <Route path="supplier-invoices" element={<SupplierInvoicesPage />} />
              <Route path="cash-registers" element={<CashRegistersPage />} />
              <Route path="bank-accounts" element={<BankAccountsPage />} />
              <Route path="hr" element={<HRPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="audit-logs" element={<AuditLogsPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
