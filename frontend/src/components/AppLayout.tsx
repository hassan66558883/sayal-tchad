import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">SEYAL-TCHAD</div>
        <nav>
          <NavLink to="/" end>
            Agences
          </NavLink>
          <NavLink to="/products">Produits</NavLink>
          <NavLink to="/partners">Clients &amp; Fournisseurs</NavLink>
          <NavLink to="/purchase-orders">Commandes d'achat</NavLink>
          <NavLink to="/imports">Importations</NavLink>
          <NavLink to="/warehouses">Entrepots</NavLink>
          <NavLink to="/stock-moves">Mouvements de stock</NavLink>
          <NavLink to="/stock-inventories">Inventaires</NavLink>
          {hasRole('direction_generale') && (
            <>
              <NavLink to="/users">Utilisateurs</NavLink>
              <NavLink to="/audit-logs">Journal d'audit</NavLink>
            </>
          )}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <span>{user?.name}</span>
          <button onClick={logout}>Deconnexion</button>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
