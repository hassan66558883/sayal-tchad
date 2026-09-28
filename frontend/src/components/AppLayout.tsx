import { useQuery } from '@tanstack/react-query'
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeftRight,
  BarChart3,
  Bell,
  Building2,
  ClipboardList,
  FileText,
  Fuel,
  Info,
  LandmarkIcon,
  LayoutDashboard,
  Menu,
  Moon,
  Package,
  PackageCheck,
  Receipt,
  ScrollText,
  Search,
  Ship,
  ShoppingCart,
  Sun,
  Target,
  Truck,
  UserCog,
  Users,
  UsersRound,
  Wallet,
  Warehouse,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { listNotifications } from '../api/notifications'
import { globalSearch, type SearchResults } from '../api/search'
import { useAuth } from '../auth/AuthContext'
import { getEffectiveTheme, setStoredTheme, type Theme } from '../theme'

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => getEffectiveTheme())

  function toggle() {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setStoredTheme(next)
    setTheme(next)
  }

  return (
    <button
      className="notif-btn"
      onClick={toggle}
      title={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
    >
      {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  )
}

const SEVERITY_ICON = {
  info: <Info size={15} />,
  warning: <AlertTriangle size={15} />,
  danger: <AlertCircle size={15} />,
}

function NotificationBell() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: listNotifications,
    refetchInterval: 60_000,
  })

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const count = notifications?.length ?? 0

  return (
    <div className="notif-box" ref={boxRef}>
      <button className="notif-btn" onClick={() => setOpen((v) => !v)} title="Notifications">
        <Bell size={18} />
        {count > 0 && <span className="notif-count">{count > 9 ? '9+' : count}</span>}
      </button>
      {open && (
        <div className="search-dropdown notif-dropdown">
          {count === 0 && <div className="search-empty">Aucune alerte.</div>}
          {notifications?.map((n) => (
            <button
              key={n.id}
              className="notif-hit"
              onClick={() => {
                navigate(n.path)
                setOpen(false)
              }}
            >
              <span className={`notif-icon ${n.severity}`}>{SEVERITY_ICON[n.severity]}</span>
              <span className="notif-text">
                <span className="notif-title">{n.title}</span>
                <span className="notif-message">{n.message}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const SEARCH_CATEGORIES: { key: keyof SearchResults; label: string }[] = [
  { key: 'partners', label: 'Clients & fournisseurs' },
  { key: 'products', label: 'Produits' },
  { key: 'invoices', label: 'Factures' },
  { key: 'sale_orders', label: 'Devis & commandes' },
  { key: 'deliveries', label: 'Livraisons' },
]

function GlobalSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResults | null>(null)
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults(null)
      return
    }
    const timer = setTimeout(() => {
      globalSearch(query.trim()).then((r) => {
        setResults(r)
        setOpen(true)
      })
    }, 250)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const hasResults = results && SEARCH_CATEGORIES.some((c) => results[c.key].length > 0)

  return (
    <div className="search-box" ref={boxRef}>
      <Search size={15} className="search-icon" />
      <input
        placeholder="Rechercher un client, produit, facture..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results && setOpen(true)}
      />
      {open && results && (
        <div className="search-dropdown">
          {!hasResults && <div className="search-empty">Aucun resultat.</div>}
          {SEARCH_CATEGORIES.map(
            (cat) =>
              results[cat.key].length > 0 && (
                <div key={cat.key}>
                  <div className="search-category">{cat.label}</div>
                  {results[cat.key].map((hit) => (
                    <button
                      key={`${cat.key}-${hit.id}`}
                      className="search-hit"
                      onClick={() => {
                        navigate(hit.path)
                        setOpen(false)
                        setQuery('')
                      }}
                    >
                      <span>{hit.label}</span>
                      <span className="search-hit-sub">{hit.sublabel}</span>
                    </button>
                  ))}
                </div>
              ),
          )}
        </div>
      )}
    </div>
  )
}

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
          {hasRole('direction_generale') && (
            <NavItem to="/receivables" icon={<AlertCircle size={17} />} label="Suivi des creances" />
          )}

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
          <GlobalSearch />
          <div className="topbar-spacer" />
          <ThemeToggle />
          <NotificationBell />
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
