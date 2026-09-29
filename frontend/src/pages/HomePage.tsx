import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function HomePage() {
  const { hasRole } = useAuth()
  return <Navigate to={hasRole('direction_generale') ? '/dashboard' : '/agences'} replace />
}
