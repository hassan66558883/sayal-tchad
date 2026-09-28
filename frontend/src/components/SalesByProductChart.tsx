import type { SalesByProduct } from '../api/dashboard'

const BAR_HEIGHT = 20
const BAR_GAP = 12
const LABEL_W = 140
const VALUE_W = 90
const CHART_W = 420

export default function SalesByProductChart({ data }: { data: SalesByProduct[] }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--text-muted)' }}>Aucune donnee pour cette periode.</p>
  }

  const maxRevenue = Math.max(...data.map((d) => d.revenue), 1)
  const totalHeight = data.length * (BAR_HEIGHT + BAR_GAP)
  const width = LABEL_W + CHART_W + VALUE_W

  return (
    <svg viewBox={`0 0 ${width} ${totalHeight}`} width="100%" height={totalHeight} role="img" aria-label="Ventes par produit">
      {data.map((d, i) => {
        const y = i * (BAR_HEIGHT + BAR_GAP)
        const barW = Math.max(4, (d.revenue / maxRevenue) * CHART_W)
        return (
          <g key={d.product_id}>
            <text x={LABEL_W - 8} y={y + BAR_HEIGHT / 2 + 4} textAnchor="end" fontSize={12} fill="var(--text)">
              {d.name.length > 20 ? `${d.name.slice(0, 18)}...` : d.name}
            </text>
            <rect x={LABEL_W} y={y} width={CHART_W} height={BAR_HEIGHT} rx={4} fill="var(--bg)" />
            <rect x={LABEL_W} y={y} width={barW} height={BAR_HEIGHT} rx={4} fill="var(--accent)">
              <title>
                {d.name}: {d.qty.toLocaleString('fr-FR')} unites, {d.revenue.toLocaleString('fr-FR')} FCFA
              </title>
            </rect>
            <text
              x={LABEL_W + barW + 8}
              y={y + BAR_HEIGHT / 2 + 4}
              fontSize={12}
              fontWeight={600}
              fill="var(--text-h)"
            >
              {d.revenue.toLocaleString('fr-FR')}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
