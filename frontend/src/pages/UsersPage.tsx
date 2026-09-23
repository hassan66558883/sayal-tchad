import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { ROLE_CODES } from '../api/roles'
import { createUser, listUsers } from '../api/users'

export default function UsersPage() {
  const queryClient = useQueryClient()
  const { data: users, isLoading } = useQuery({ queryKey: ['users'], queryFn: listUsers })

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [roleCodes, setRoleCodes] = useState<string[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setName('')
      setEmail('')
      setPassword('')
      setRoleCodes([])
      setFormError(null)
    },
    onError: () => setFormError('Impossible de creer cet utilisateur (email deja utilise ?).'),
  })

  function toggleRole(code: string) {
    setRoleCodes((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate({ name, email, password, role_codes: roleCodes })
  }

  return (
    <div>
      <h1>Utilisateurs</h1>
      {isLoading && <p>Chargement...</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Email</th>
            <th>Roles</th>
          </tr>
        </thead>
        <tbody>
          {users?.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>{u.is_superuser ? 'Superuser' : u.roles.map((r) => r.label).join(', ') || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <form className="inline-form" onSubmit={handleSubmit}>
        <h2>Nouvel utilisateur</h2>
        <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Mot de passe"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <fieldset className="role-picker">
          <legend>Roles</legend>
          {ROLE_CODES.map(([code, label]) => (
            <label key={code}>
              <input
                type="checkbox"
                checked={roleCodes.includes(code)}
                onChange={() => toggleRole(code)}
              />
              {label}
            </label>
          ))}
        </fieldset>
        <button type="submit" disabled={mutation.isPending}>
          Creer
        </button>
        {formError && <p className="error">{formError}</p>}
      </form>
    </div>
  )
}
