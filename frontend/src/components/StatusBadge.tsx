type Tone = 'success' | 'warning' | 'danger' | 'gold' | 'muted'

const STATUS_META: Record<string, { label: string; tone: Tone }> = {
  // sale / purchase orders
  devis: { label: 'Devis', tone: 'muted' },
  proforma: { label: 'Proforma', tone: 'muted' },
  commande: { label: 'Commande', tone: 'gold' },
  terminee: { label: 'Terminee', tone: 'success' },
  annulee: { label: 'Annulee', tone: 'danger' },

  // invoices / expenses / stock moves & inventories
  draft: { label: 'Brouillon', tone: 'muted' },
  validated: { label: 'Validee', tone: 'success' },
  cancelled: { label: 'Annulee', tone: 'danger' },

  // payments
  confirmed: { label: 'Confirme', tone: 'success' },

  // payment_state
  not_paid: { label: 'Impayee', tone: 'danger' },
  partially_paid: { label: 'Partielle', tone: 'warning' },
  paid: { label: 'Payee', tone: 'success' },

  // delivery routes / deliveries
  planifiee: { label: 'Planifiee', tone: 'muted' },
  chargee: { label: 'Chargee', tone: 'warning' },
  en_livraison: { label: 'En livraison', tone: 'gold' },
  livree: { label: 'Livree', tone: 'success' },
  cloturee: { label: 'Cloturee', tone: 'success' },
  partielle: { label: 'Partielle', tone: 'warning' },
  probleme: { label: 'Probleme', tone: 'danger' },

  // cash sessions
  open: { label: 'Ouverte', tone: 'success' },
  closed: { label: 'Fermee', tone: 'muted' },

  // leave requests
  en_attente: { label: 'En attente', tone: 'warning' },
  approuvee: { label: 'Approuvee', tone: 'success' },
  refusee: { label: 'Refusee', tone: 'danger' },

  // imports
  nouveau: { label: 'Nouveau', tone: 'muted' },
  expedie: { label: 'Expedie', tone: 'gold' },
  arrive: { label: 'Arrive', tone: 'gold' },
  douane: { label: 'En douane', tone: 'warning' },
  receptionne: { label: 'Receptionne', tone: 'success' },
}

export default function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] ?? { label: status, tone: 'muted' as Tone }
  return <span className={`badge badge-${meta.tone}`}>{meta.label}</span>
}
