import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { t } from '../i18n'
import { Info } from './Learn'
import type { MonthClimate } from '../types'

export function MonthlyChart({ months }: { months: MonthClimate[] }) {
  const data = months.map((m) => ({
    name: t.months[m.month - 1],
    label: t.monthNames[m.month - 1],
    precip: m.precip_mm,
    et0: m.et0_mm,
    tmean: m.tmean_c,
  }))
  return (
    <section className="card">
      <h2>
        {t.monthlyTitle} <Info term="water_balance" />
      </h2>
      <div className="chart">
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
            <YAxis yAxisId="mm" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="c" orientation="right" tick={{ fontSize: 11 }} width={32} />
            <Tooltip labelFormatter={(_, p) => p?.[0]?.payload?.label ?? ''} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar yAxisId="mm" dataKey="precip" name={t.precip} fill="var(--rain)" radius={[3, 3, 0, 0]} />
            <Bar yAxisId="mm" dataKey="et0" name={t.et0} fill="var(--et0)" radius={[3, 3, 0, 0]} />
            <Line yAxisId="c" dataKey="tmean" name={t.tmean} stroke="var(--temp)" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
