import {
  ArrowLeftRight,
  BarChart3,
  Building2,
  ClipboardList,
  FileText,
  Fuel,
  LandmarkIcon,
  LayoutDashboard,
  Menu,
  Package,
  PackageCheck,
  Receipt,
  ScrollText,
  Ship,
  ShoppingCart,
  Target,
  Truck,
  UserCog,
  Users,
  UsersRound,
  Wallet,
  Warehouse,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

function NavItem({ to, end, icon, label }: { to: string; end?: boolean; icon: React.ReactNode; label: string }) {
  return (
    <NavLink to={to} end={end} data-label={label}>
      {icon}
      <span>{label}</span>
    </NavLink>
  )
}

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth()
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sayal_sidebar_collapsed') === '1')
  const [mobileOpen, setMobileOpen] = useState(false)

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem('sayal_sidebar_collapsed', next ? '1' : '0')
      return next
    })
  }

  return (
    <div className="app-shell">
      <div className={`sidebar-backdrop ${mobileOpen ? 'open' : ''}`} onClick={() => setMobileOpen(false)} />
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="brand-row">
          <div className="brand">
            <span className="brand-mark">S</span>
            <span>SAYAL ERP</span>
          </div>
          <button
            className="collapse-btn"
            onClick={() => (mobileOpen ? setMobileOpen(false) : toggleCollapsed())}
            title={mobileOpen ? 'Fermer le menu' : 'Reduire le menu'}
          >
            {mobileOpen ? <X size={15} /> : <Menu size={15} />}
          </button>
        </div>
        <nav>
          <NavItem to="/" end icon={<Building2 size={17} />} label="Agences" />
          {hasRole('direction_generale') && (
            <NavItem to="/dashboard" icon={<LayoutDashboard size={17} />} label="Tableau de bord" />
          )}

          <div className="nav-section">Achats &amp; stock</div>
          <NavItem to="/products" icon={<Package size={17} />} label="Produits" />
          <NavItem to="/purchase-orders" icon={<ShoppingCart size={17} />} label="Commandes d'achat" />
          <NavItem to="/imports" icon={<Ship size={17} />} label="Importations" />
          <NavItem to="/warehouses" icon={<Warehouse size={17} />} label="Entrepots" />
          <NavItem to="/stock-moves" icon={<ArrowLeftRight size={17} />} label="Mouvements de stock" />
          <NavItem to="/stock-inventories" icon={<ClipboardList size={17} />} label="Inventaires" />

          <div className="nav-section">Ventes</div>
          <NavItem to="/sale-orders" icon={<FileText size={17} />} label="Devis &amp; commandes" />
          <NavItem to="/invoices" icon={<Receipt size={17} />} label="Factures" />

          <div className="nav-section">Commercial</div>
          <NavItem to="/partners" icon={<Users size={17} />} label="Clients &amp; fournisseurs" />
          <NavItem to="/commercial" icon={<Target size={17} />} label="Commercial" />

          <div className="nav-section">Flotte &amp; distribution</div>
          <NavItem to="/fleet" icon={<Truck size={17} />} label="Vehicules &amp; chauffeurs" />
          <NavItem to="/fleet-operations" icon={<Fuel size={17} />} label="Carburant &amp; entretien" />
          <NavItem to="/delivery-routes" icon={<PackageCheck size={17} />} label="Tournees" />
          <NavItem to="/deliveries" icon={<PackageCheck size={17} />} label="Mes livraisons" />

          <div className="nav-section">Finance</div>
          <NavItem to="/supplier-invoices" icon={<Receipt size={17} />} label="Dettes fournisseurs" />
          <NavItem to="/cash-registers" icon={<Wallet size={17} />} label="Caisse" />
          <NavItem to="/bank-accounts" icon={<LandmarkIcon size={17} />} label="Banque" />

          <div className="nav-section">RH &amp; rapports</div>
          <NavItem to="/hr" icon={<UsersRound size={17} />} label="Ressources humaines" />
          <NavItem to="/reports" icon={<BarChart3 size={17} />} label="Rapports" />

          {hasRole('direction_generale') && (
            <>
              <div className="nav-section">Administration</div>
              <NavItem to="/users" icon={<UserCog size={17} />} label="Utilisateurs" />
              <NavItem to="/audit-logs" icon={<ScrollText size={17} />} label="Journal d'audit" />
            </>
          )}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="mobile-menu-btn" onClick={() => setMobileOpen(true)} title="Menu">
            <Menu size={18} />
          </button>
          <div className="topbar-spacer" />
          <span className="user-avatar">{(user?.name ?? '?').slice(0, 1).toUpperCase()}</span>
          <span className="user-name">{user?.name}</span>
          <button className="logout-btn" onClick={logout}>
            Deconnexion
          </button>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
